"""
Vision API Celery Tasks (v2 — 피드백 반영)

개선사항:
1. 입력 검증 에러 vs API 에러 분리 → 잘못된 입력은 retry 안 함
2. 공통 실행 로직(_run_vision_task)으로 묶기
3. 성공/실패 반환 형식 통일
4. 로그 정리
"""

import asyncio
import base64
import json
import logging
import os
import time

import redis as sync_redis

from ai.celery_app import celery_app

from .client import ALLOWED_MEDIA_TYPES
from .exercise_service import ExerciseService
from .meal_service import MealService

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Pub/Sub 발행 Redis 클라이언트 (DB 3)
# ──────────────────────────────────────────────
_REDIS_BASE = os.getenv("REDIS_URL", "redis://localhost:6379/0").rsplit("/", 1)[0]
_PUBSUB_REDIS_URL = os.getenv("REDIS_PUBSUB_URL", _REDIS_BASE + "/3")
_pubsub_redis = sync_redis.from_url(_PUBSUB_REDIS_URL, decode_responses=True)


def _publish_result(task_id: str, payload: dict) -> None:
    """태스크 완료 결과를 Redis Pub/Sub 채널에 발행한다."""
    channel = f"task:result:{task_id}"
    try:
        _pubsub_redis.publish(channel, json.dumps(payload))
        logger.info("Pub/Sub 발행 완료 - channel: %s", channel)
    except Exception as pub_err:
        logger.warning("Pub/Sub 발행 실패 (무시) - %s", pub_err)

# ──────────────────────────────────────────────
# 서비스 인스턴스 (Worker 프로세스당 1개)
# ──────────────────────────────────────────────
meal_service = MealService()
exercise_service = ExerciseService()


# ══════════════════════════════════════════════
# 1. 입력 검증 (실패 시 retry 안 함)
# ══════════════════════════════════════════════
# 비유: 주문서 주소가 틀리면 배달을 100번 보내도 소용없음
#       → 바로 "주소 확인해주세요" 반환

class InvalidInputError(Exception):
    """재시도해도 해결 안 되는 입력 오류"""
    pass


def validate_input(image_base64: str, media_type: str) -> bytes:
    """
    입력 검증 + base64 디코딩

    검증 통과 → image_bytes 반환
    검증 실패 → InvalidInputError 발생 (retry 안 함)
    """
    # 1) media_type 검증
    if media_type not in ALLOWED_MEDIA_TYPES:
        raise InvalidInputError(
            f"지원하지 않는 이미지 형식: {media_type}. "
            f"지원 형식: {', '.join(ALLOWED_MEDIA_TYPES)}"
        )

    # 2) base64 문자열 검증
    if not image_base64 or not isinstance(image_base64, str):
        raise InvalidInputError("이미지 데이터가 비어있거나 형식이 잘못되었습니다.")

    # 3) base64 디코딩
    try:
        image_bytes = base64.b64decode(image_base64)
    except Exception as decode_err:
        raise InvalidInputError("base64 디코딩 실패 — 이미지 데이터가 손상되었습니다.") from decode_err

    # 4) 디코딩된 데이터 크기 검증
    if len(image_bytes) == 0:
        raise InvalidInputError("이미지 데이터가 비어있습니다.")

    return image_bytes


# ══════════════════════════════════════════════
# 2. 통일된 반환 형식
# ══════════════════════════════════════════════
# 성공이든 실패든 같은 구조로 반환
# → FastAPI에서 분기 처리가 깔끔해짐

def success_response(task_name: str, task_id: str, result: dict) -> dict:
    """성공 응답 형식"""
    return {
        "status": "success",
        "task_name": task_name,
        "task_id": task_id,
        "data": result,         # {"result": {...}}
        "error": None,
    }


def fail_response(task_name: str, task_id: str, error_message: str) -> dict:
    """실패 응답 형식"""
    return {
        "status": "failed",
        "task_name": task_name,
        "task_id": task_id,
        "data": None,
        "error": error_message,
    }


# ══════════════════════════════════════════════
# 3. 공통 실행 로직
# ══════════════════════════════════════════════
# 세 task 모두 같은 패턴:
#   입력 검증 → 서비스 호출 → 결과 반환
# 이걸 하나로 묶어서 중복 제거

def _run_vision_task(self, task_name: str, image_base64: str, media_type: str, service_call):
    """
    공통 task 실행 함수

    Args:
        self: Celery task 인스턴스 (bind=True)
        task_name: 작업 이름 (로그용)
        image_base64: 이미지 base64 문자열
        media_type: MIME 타입
        service_call: 실행할 함수 (lambda로 전달)
                      예: lambda bytes: meal_service.analyze_free(bytes, media_type)

    Returns:
        dict: 통일된 응답 형식 (success_response 또는 fail_response)
    """
    task_id = self.request.id
    logger.info(f"[{task_name}] 시작 | task_id={task_id}")

    # ── Step 1: 입력 검증 (실패 시 retry 안 함) ──
    try:
        image_bytes = validate_input(image_base64, media_type)
    except InvalidInputError as e:
        logger.warning(f"[{task_name}] 입력 오류 (retry 안 함) | task_id={task_id} | {e}")
        return fail_response(task_name, task_id, str(e))

    # ── Step 2: 서비스 호출 (실패 시 retry 함) ──
    try:
        _t0 = time.perf_counter()
        result = asyncio.run(service_call(image_bytes))
        llm_ms = round((time.perf_counter() - _t0) * 1000)
        logger.info(f"[{task_name}] 완료 | llm_ms={llm_ms} | task_id={task_id}")
        response = success_response(task_name, task_id, result)

        # Pub/Sub 발행 (SSE 구독 중인 클라이언트에 실시간 전달)
        _publish_result(task_id, response)

        return response

    except Exception as exc:
        logger.error(f"[{task_name}] API 오류 (retry 시도) | task_id={task_id} | {exc}")
        raise self.retry(exc=exc) from exc


# ══════════════════════════════════════════════
# 4. Task 정의
# ══════════════════════════════════════════════

def _retrieve_nutrition_context(risk_grade: str, risk_factors: str) -> str:
    """
    nutrition_knowledge 컬렉션에서 RAG 검색을 수행하고 포맷된 컨텍스트를 반환한다.

    risk_grade가 없으면 필터 없이 전체 문서에서 검색한다.
    실패 시 빈 문자열을 반환하여 서비스 중단을 방지한다.
    """
    try:
        from ai.core import config
        from ai.rag.retriever import build_nutrition_rag_query, format_context_for_prompt, retrieve_health_context

        rag_query = build_nutrition_rag_query(risk_grade, risk_factors)
        rag_chunks = retrieve_health_context(
            query=rag_query,
            risk_grade=risk_grade,
            collection=config.QDRANT_COLLECTION_NUTRITION,
        )
        return format_context_for_prompt(rag_chunks)
    except Exception as e:
        logger.warning("영양 RAG 검색 실패 (무시): %s", e)
        return ""


# ── Task 1: 식단 무료 분석 ──
@celery_app.task(
    name="vision.analyze_meal_free",
    bind=True,
    max_retries=2,
    default_retry_delay=5,
)
def analyze_meal_free(self, image_base64: str, media_type: str, risk_factors: str = "", risk_grade: str = ""):
    """
    식단 무료 분석 (+100pt)

    FastAPI에서 호출:
        from ai.vision.tasks import analyze_meal_free
        task = analyze_meal_free.delay(image_base64, media_type, risk_factors, risk_grade)
        result = task.get()  # 또는 task.id로 상태 조회
    """
    # 전체 태스크 시작 시각
    task_start = time.perf_counter()

    # RAG 컨텍스트 검색 (risk_grade 없으면 필터 없이 전체 검색)
    _t0 = time.perf_counter()
    rag_context = _retrieve_nutrition_context(risk_grade, risk_factors)
    rag_search_ms = round((time.perf_counter() - _t0) * 1000)
    logger.info("무료_분석 RAG 검색 완료 - %dms", rag_search_ms)

    # RAG 적용 결과
    response = _run_vision_task(
        self=self,
        task_name="식단_무료_분석",
        image_base64=image_base64,
        media_type=media_type,
        service_call=lambda img_bytes: meal_service.analyze_free(
            image_bytes=img_bytes,
            media_type=media_type,
            risk_factors=risk_factors,
            rag_context=rag_context,
        ),
    )

    # 구간별 소요 시간 로그 (응답에는 포함하지 않음)
    if response.get("status") == "success":
        total_ms = round((time.perf_counter() - task_start) * 1000)
        logger.info("무료_분석 구간 시간 - rag: %dms, total: %dms", rag_search_ms, total_ms)

    return response


# ── Task 2: 식단 유료 상세 리포트 ──
@celery_app.task(
    name="vision.analyze_meal_paid",
    bind=True,
    max_retries=2,
    default_retry_delay=5,
)
def analyze_meal_paid(self, image_base64: str, media_type: str, risk_factors: str = "", risk_grade: str = ""):
    """
    식단 유료 상세 리포트 (-300pt)

    FastAPI에서 호출:
        task = analyze_meal_paid.delay(image_base64, media_type, risk_factors, risk_grade)
    """
    # 전체 태스크 시작 시각
    task_start = time.perf_counter()

    # RAG 컨텍스트 검색 (risk_grade 없으면 필터 없이 전체 검색)
    _t0 = time.perf_counter()
    rag_context = _retrieve_nutrition_context(risk_grade, risk_factors)
    rag_search_ms = round((time.perf_counter() - _t0) * 1000)
    logger.info("유료_분석 RAG 검색 완료 - %dms", rag_search_ms)

    # RAG 적용 결과
    response = _run_vision_task(
        self=self,
        task_name="식단_유료_분석",
        image_base64=image_base64,
        media_type=media_type,
        service_call=lambda img_bytes: meal_service.analyze_paid(
            image_bytes=img_bytes,
            media_type=media_type,
            risk_factors=risk_factors,
            rag_context=rag_context,
        ),
    )

    # 구간별 소요 시간 로그 (응답에는 포함하지 않음)
    if response.get("status") == "success":
        total_ms = round((time.perf_counter() - task_start) * 1000)
        logger.info("유료_분석 구간 시간 - rag: %dms, total: %dms", rag_search_ms, total_ms)

    return response


# ── Task 3: 운동 캡처 인증 ──
@celery_app.task(
    name="vision.analyze_exercise",
    bind=True,
    max_retries=2,
    default_retry_delay=5,
)
def analyze_exercise(self, image_base64: str, media_type: str):
    """
    운동 앱 스크린샷 인증 (+100pt)

    FastAPI에서 호출:
        task = analyze_exercise.delay(image_base64, media_type)
    """
    return _run_vision_task(
        self=self,
        task_name="운동_캡처_인증",
        image_base64=image_base64,
        media_type=media_type,
        service_call=lambda img_bytes: exercise_service.analyze(
            image_bytes=img_bytes,
            media_type=media_type,
        ),
    )
