"""
ML1 Celery Task 정의
건강검진 수치 → XGBoost 위험도 예측 + ChatGPT 건강 코멘트 생성
"""

import hashlib
import json
import logging
import math
import os

import redis

from ai.celery_app import celery_app
from ai.workers.worker import ml1_comment, ml1_predict

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Redis 클라이언트 설정
# DB 2: ML1 분석 결과 캐시 (24시간 TTL)
# DB 3: Pub/Sub 발행 (태스크 완료 실시간 알림)
# ──────────────────────────────────────────────
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_redis_base = REDIS_URL.rsplit("/", 1)[0]

CACHE_REDIS_URL = os.getenv("REDIS_CACHE_URL", _redis_base + "/2")
PUBSUB_REDIS_URL = os.getenv("REDIS_PUBSUB_URL", _redis_base + "/3")

cache_redis = redis.from_url(CACHE_REDIS_URL, decode_responses=True)
pubsub_redis = redis.from_url(PUBSUB_REDIS_URL, decode_responses=True)

# 캐시 TTL: 24시간 (전체 결과 캐시)
CACHE_TTL = 86400

# LLM 코멘트 캐시 TTL: 7일 (전체 캐시보다 길게 설정해 재사용률 극대화)
LLM_CACHE_TTL = 604800

# LLM 프롬프트 버전: prompt.py 변경 시 올려 기존 캐시 무효화
LLM_PROMPT_VERSION = "v1"


def _publish_result(task_id: str, payload: dict) -> None:
    """태스크 완료 결과를 Redis Pub/Sub 채널에 발행한다."""
    channel = f"task:result:{task_id}"
    try:
        pubsub_redis.publish(channel, json.dumps(payload))
        logger.info("Pub/Sub 발행 완료 - channel: %s", channel)
    except Exception as pub_err:
        logger.warning("Pub/Sub 발행 실패 (무시) - %s", pub_err)


def _build_cache_key(user_data: dict, nickname: str, challenge_days: int) -> str:
    """전체 결과 캐시 키 생성 (입력 데이터의 MD5 해시)"""
    key_source = json.dumps({"user_data": user_data, "nickname": nickname, "challenge_days": challenge_days}, sort_keys=True)
    return f"ml1:cache:{hashlib.md5(key_source.encode()).hexdigest()}"


def _build_llm_cache_key(predict_result: dict, user_data: dict, challenge_days: int) -> str:
    """LLM 코멘트 캐시 키 생성.

    의학적으로 다른 조언을 유발하는 필드만 포함한다.
    - 포함: risk_grade, age(5세 버킷), smoke, alco, top_risk_factors, challenge_days(7일 버킷)
    - 제외: nickname(인사말만 영향), risk_percent(소수점 차이 무의미), heart_age(risk_grade+age에서 파생)
    """
    key_source = json.dumps(
        {
            "v": LLM_PROMPT_VERSION,
            "risk_grade": predict_result["risk_grade"],
            "age_bucket": math.floor(user_data["age"] / 5) * 5,
            "smoke": user_data["smoke"],
            "alco": user_data["alco"],
            "top_risk_factors": sorted(predict_result["top_risk_factors"]),
            "challenge_bucket": math.floor(challenge_days / 7) * 7,
        },
        sort_keys=True,
    )
    return f"ml1:llm_cache:{hashlib.md5(key_source.encode()).hexdigest()}"


# ──────────────────────────────────────────────
# ML1 분석 Celery Task
# ──────────────────────────────────────────────
@celery_app.task(
    name="ml1.analyze_health",
    bind=True,
    max_retries=2,
    default_retry_delay=5,
)
def analyze_health(self, user_data: dict, nickname: str = "사용자", challenge_days: int = 0) -> dict:
    """
    건강검진 수치 → XGBoost 예측 + GPT 코멘트 (Celery task)

    Args:
        user_data: ml1_run 입력 형식 (age, gender, height, weight, ap_hi, ap_lo, ...)
        nickname: 사용자 닉네임
        challenge_days: 챌린지 진행일

    Returns:
        통일된 응답 형식 (status, task_id, data, error)
    """
    task_id = self.request.id
    logger.info("ML1 분석 시작 - task_id: %s", task_id)

    try:
        # Step 1: XGBoost 예측 (< 0.1초)
        logger.info("XGBoost 예측 시작 - task_id: %s", task_id)
        predict_result = ml1_predict(user_data)
        logger.info("XGBoost 예측 완료 - risk_grade: %s, task_id: %s", predict_result["risk_grade"], task_id)

        # Step 2: LLM 코멘트 캐시 확인 (risk_grade + 핵심 요인 기준)
        llm_cache_key = _build_llm_cache_key(predict_result, user_data, challenge_days)
        cached_comment_raw = cache_redis.get(llm_cache_key)

        if cached_comment_raw:
            logger.info("LLM 캐시 히트 - risk_grade: %s, task_id: %s", predict_result["risk_grade"], task_id)
            comment_result = json.loads(cached_comment_raw)
        else:
            # Step 3: OpenAI 호출 (4~5초)
            logger.info("LLM 캐시 미스 - OpenAI 호출 시작, task_id: %s", task_id)
            user_info = {
                "nickname": nickname,
                "age": user_data["age"],
                "risk_percent": predict_result["risk_percent"],
                "risk_grade": predict_result["risk_grade"],
                "heart_age": predict_result["heart_age"],
                "top_risk_factors": predict_result["top_risk_factors"],
                "smoke": user_data["smoke"],
                "alco": user_data["alco"],
                "challenge_days": challenge_days,
            }
            comment_result = ml1_comment(user_info)
            logger.info("OpenAI 호출 완료 - task_id: %s", task_id)

            # LLM 코멘트 캐시 저장 (TTL 7일)
            try:
                cache_redis.setex(llm_cache_key, LLM_CACHE_TTL, json.dumps(comment_result))
                logger.info("LLM 캐시 저장 완료 - key: %s", llm_cache_key)
            except Exception as cache_err:
                logger.warning("LLM 캐시 저장 실패 (무시) - %s", cache_err)

        result = {
            "ml1_predict": predict_result,
            "ml1_comment": comment_result,
        }

        # 전체 결과 캐시 저장 (TTL 24시간, 기존 동작 유지)
        cache_key = _build_cache_key(user_data, nickname, challenge_days)
        try:
            cache_redis.setex(cache_key, CACHE_TTL, json.dumps(result))
            logger.info("ML1 전체 캐시 저장 완료 - key: %s", cache_key)
        except Exception as cache_err:
            logger.warning("ML1 전체 캐시 저장 실패 (무시) - %s", cache_err)

        result_payload = {
            "status": "success",
            "task_id": task_id,
            "data": result,
            "error": None,
        }

        # Pub/Sub 발행 (롱폴링 대기 중인 클라이언트에 실시간 전달)
        _publish_result(task_id, result_payload)

        logger.info("ML1 분석 완료 - task_id: %s", task_id)
        return result_payload

    except Exception as exc:
        logger.error("ML1 분석 실패 (retry 시도) - task_id: %s, error: %s", task_id, exc)
        raise self.retry(exc=exc) from exc
    
# ──────────────────────────────────────────────
# ML1 챌린지 달성 후 재계산 Celery Task
# ──────────────────────────────────────────────
@celery_app.task(
    name="ml1.recalculate_risk",
    bind=True,
    max_retries=2,
    default_retry_delay=5,
)
def recalculate_health(self, user_data: dict, completed_challenges: list, nickname: str = "사용자") -> dict:
    """
    챌린지 달성 후 위험도 재계산

    Args:
        user_data: 사용자 건강 데이터
        completed_challenges: ['smoke_7days', 'active_7days']
        nickname: 사용자 닉네임
    """
    from ai.workers.predict import recalculate_risk

    task_id = self.request.id
    logger.info("ML1 재계산 시작 - task_id: %s", task_id)

    try:
        result = recalculate_risk(user_data, completed_challenges)

        result_payload = {
            "status": "success",
            "task_id": task_id,
            "data": result,
            "error": None,
        }

        _publish_result(task_id, result_payload)
        logger.info("ML1 재계산 완료 - task_id: %s", task_id)
        return result_payload

    except Exception as exc:
        logger.error("ML1 재계산 실패 - task_id: %s, error: %s", task_id, exc)
        raise self.retry(exc=exc) from exc


# ──────────────────────────────────────────────
# RAG 챌린지 추천 Celery Task
# ──────────────────────────────────────────────
@celery_app.task(
    name="ml1.recommend_challenges",
    bind=True,
    max_retries=2,
    default_retry_delay=5,
)
def recommend_challenges(
    self,
    user_profile: dict,
    prediction: dict,
    challenges: list,
    active_challenge_ids: list,
    completed_challenge_ids: list,
) -> dict:
    """
    RAG 기반 챌린지 추천

    Args:
        user_profile: {nickname, age, gender}
        prediction: {top_risk_factors, risk_level, risk_percent, cvd_age}
        challenges: 전체 챌린지 목록 [{id, title, category, target_risk_factors, expected_effect, description}]
        active_challenge_ids: 현재 참여 중인 챌린지 ID
        completed_challenge_ids: 완료한 챌린지 ID

    Returns:
        {status, task_id, data: [{challenge_id, title, reason}], error}
    """
    from ai.workers.recommender import embed_and_store_challenges, generate_recommendations, retrieve_top_k

    task_id = self.request.id
    logger.info("RAG 챌린지 추천 시작 - task_id: %s", task_id)

    try:
        # 이미 참여/완료한 챌린지 제외
        exclude_ids = set(active_challenge_ids + completed_challenge_ids)
        available = [c for c in challenges if c["id"] not in exclude_ids]

        if not available:
            result_payload = {"status": "success", "task_id": task_id, "data": [], "error": None}
            _publish_result(task_id, result_payload)
            return result_payload

        # Step 1: 챌린지 임베딩 (캐시 없는 것만 새로 생성)
        new_count = embed_and_store_challenges(available)
        logger.info("챌린지 임베딩 완료 - 신규: %d개, task_id: %s", new_count, task_id)

        # Step 2: 유저 프로필 임베딩 → 유사도 검색 → Top K
        top_challenges = retrieve_top_k(user_profile, prediction, available)
        logger.info("Top %d 챌린지 검색 완료 - task_id: %s", len(top_challenges), task_id)

        # Step 3: GPT 추천 이유 생성
        recommendations = generate_recommendations(user_profile, prediction, top_challenges)
        logger.info("GPT 추천 완료 - %d개, task_id: %s", len(recommendations), task_id)

        result_payload = {
            "status": "success",
            "task_id": task_id,
            "data": recommendations,
            "error": None,
        }
        _publish_result(task_id, result_payload)
        return result_payload

    except Exception as exc:
        logger.error("RAG 추천 실패 - task_id: %s, error: %s", task_id, exc)
        raise self.retry(exc=exc) from exc