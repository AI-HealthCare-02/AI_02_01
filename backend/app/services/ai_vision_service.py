"""
ML2 Vision API Service — Celery 태스크 호출 및 결과 조회

역할: 라우터에서 받은 데이터 → Celery ml2 큐에 태스크 등록 → task_id 반환
      결과 조회 시 SUCCESS면 cv_analysis_logs DB에 저장 (ML1 패턴 동일)

주의: backend 컨테이너와 ai-worker 컨테이너는 분리되어 있으므로
      ai 패키지를 직접 import하지 않고, 이름 기반 send_task()로 호출한다.
"""

import json
import logging

from celery import Celery
from celery.result import AsyncResult
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Config
from app.models.cv_analysis_logs import AnalysisTypeEnum
from app.repositories.cv_analysis_log_repository import CvAnalysisLogRepository

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Celery 클라이언트 역할별 분리
#
# send_task() 호출 시 Redis backend가 설정되어 있으면
# Pub/Sub result consumer를 즉시 구독 시도 → 연결 실패 시 RuntimeError 발생
#
# 해결: 발송과 결과 조회를 별도 앱으로 분리
#   - _celery_sender: broker만 설정 → Pub/Sub 구독 없음
#   - _celery_result: broker + backend 설정 → AsyncResult 조회 전용
# ──────────────────────────────────────────────
_config = Config()

# 태스크 발송 전용 (Pub/Sub result consumer 미설정)
_celery_sender = Celery(broker=_config.CELERY_BROKER_URL)

# 결과 조회 전용 (backend 필요)
_celery_result = Celery(
    broker=_config.CELERY_BROKER_URL,
    backend=_config.CELERY_BACKEND_URL,
)

# task_meta TTL: 24시간
_TASK_META_TTL = 86400


class AIVisionService:
    """ML2 Vision API Celery 태스크 호출 서비스"""

    def __init__(self, session: AsyncSession, redis: Redis):
        self._cv_log_repo = CvAnalysisLogRepository(session)
        self._redis = redis

    # ── 식단 무료 분석 (+100pt) ──

    async def enqueue_meal_free(self, image_base64: str, media_type: str, user_id: int, image_url: str | None = None, risk_factors: str = "") -> str:
        task = _celery_sender.send_task(
            "vision.analyze_meal_free",
            args=[image_base64, media_type, risk_factors, risk_grade],
        )
        await self._save_task_meta(task.id, user_id, AnalysisTypeEnum.DIET, image_url)
        return task.id

    # ── 식단 유료 리포트 (-300pt) ──

    async def enqueue_meal_paid(self, image_base64: str, media_type: str, user_id: int, image_url: str | None = None, risk_factors: str = "") -> str:
        task = _celery_sender.send_task(
            "vision.analyze_meal_paid",
            args=[image_base64, media_type, risk_factors, risk_grade],
        )
        await self._save_task_meta(task.id, user_id, AnalysisTypeEnum.DIET, image_url)
        return task.id

    # ── 운동 캡처 인증 (+100pt) ──

    async def enqueue_exercise(self, image_base64: str, media_type: str, user_id: int, image_url: str | None = None) -> str:
        task = _celery_sender.send_task(
            "vision.analyze_exercise",
            args=[image_base64, media_type],
        )
        await self._save_task_meta(task.id, user_id, AnalysisTypeEnum.EXERCISE, image_url)
        return task.id

    # ── 결과 조회 (공통) ──

    async def get_task_result(self, task_id: str) -> dict:
        """Celery 태스크 상태 및 결과를 조회한다. SUCCESS 시 DB 저장."""
        result = AsyncResult(task_id, app=_celery_result)

        if result.state == "PENDING":
            return {"task_id": task_id, "status": "PENDING", "result": None, "error": None}

        if result.state == "SUCCESS":
            data = result.result
            # Celery state=SUCCESS여도 내부 payload가 failed일 수 있으므로 status 체크
            if isinstance(data, dict) and data.get("status") == "success":
                await self._persist_cv_analysis_log(task_id, data.get("data"))
                return {"task_id": task_id, "status": "SUCCESS", "result": data, "error": None}
            # 분석 자체가 실패한 경우 (예: 잘못된 이미지)
            error_msg = data.get("error") if isinstance(data, dict) else "분석 실패"
            return {"task_id": task_id, "status": "FAILURE", "result": None, "error": error_msg}

        if result.state == "FAILURE":
            return {"task_id": task_id, "status": "FAILURE", "result": None, "error": str(result.result)}

        # RETRY, STARTED 등 기타 상태
        return {"task_id": task_id, "status": result.state, "result": None, "error": None}

    # ──────────────────────────────────────────────
    # private
    # ──────────────────────────────────────────────

    async def _save_task_meta(self, task_id: str, user_id: int, analysis_type: AnalysisTypeEnum, image_url: str | None = None) -> None:
        """enqueue 시 Redis에 task_meta 저장 (결과 조회 시 DB 저장에 사용)"""
        meta = json.dumps({"user_id": user_id, "analysis_type": analysis_type.value, "image_url": image_url})
        await self._redis.set(f"vision:task_meta:{task_id}", meta, ex=_TASK_META_TTL)

    async def _persist_cv_analysis_log(self, task_id: str, result_data: dict | None) -> None:
        """
        Celery task 완료 시 분석 결과를 cv_analysis_logs DB에 저장.
        - Redis task_meta에서 user_id, analysis_type 조회
        - 중복 저장 방지: vision:result_saved:{task_id} 플래그 확인
        - DB 저장 실패해도 결과 응답에 영향 없도록 try/except 처리
        """
        if not result_data:
            return

        # 중복 저장 방지
        saved_flag = await self._redis.get(f"vision:result_saved:{task_id}")
        if saved_flag:
            return

        # task_meta 조회
        raw_meta = await self._redis.get(f"vision:task_meta:{task_id}")
        if not raw_meta:
            logger.warning("vision task_meta 없음 - task_id: %s", task_id)
            return

        meta = json.loads(raw_meta)
        user_id = meta.get("user_id")
        analysis_type = meta.get("analysis_type")

        if not user_id or not analysis_type:
            logger.warning("vision task_meta 필드 누락 - task_id: %s, meta: %s", task_id, meta)
            return

        try:
            analysis_type_enum = AnalysisTypeEnum(analysis_type)
            await self._cv_log_repo.create({
                "user_id": user_id,
                "analysis_type": analysis_type_enum,
                "image_url": meta.get("image_url"),
                "result_json": result_data,
            })
            await self._redis.set(f"vision:result_saved:{task_id}", "1", ex=_TASK_META_TTL)
            logger.info("cv_analysis_log DB 저장 완료 - task_id: %s, user_id: %d", task_id, user_id)
        except Exception as e:
            logger.error("cv_analysis_log DB 저장 실패 - task_id: %s, error: %s", task_id, e)
