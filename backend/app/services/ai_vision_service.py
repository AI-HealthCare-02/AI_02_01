"""
ML2 Vision API Service — Celery 태스크 호출 및 결과 조회

역할: 라우터에서 받은 데이터 → Celery ml2 큐에 태스크 등록 → task_id 반환

주의: backend 컨테이너와 ai-worker 컨테이너는 분리되어 있으므로
      ai 패키지를 직접 import하지 않고, 이름 기반 send_task()로 호출한다.
"""

from celery import Celery
from celery.result import AsyncResult

from app.core.config import Config

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


# ══════════════════════════════════════════════
# Service 클래스
# ══════════════════════════════════════════════


class AIVisionService:
    """ML2 Vision API Celery 태스크 호출 서비스"""

    # ── 식단 무료 분석 (+100pt) ──

    @staticmethod
    def enqueue_meal_free(image_base64: str, media_type: str, risk_factors: str = "") -> str:
        """식단 무료 분석 태스크를 큐에 등록하고 task_id를 반환한다."""
        task = _celery_sender.send_task(
            "vision.analyze_meal_free",
            args=[image_base64, media_type, risk_factors],
        )
        return task.id

    # ── 식단 유료 리포트 (-300pt) ──

    @staticmethod
    def enqueue_meal_paid(image_base64: str, media_type: str, risk_factors: str = "") -> str:
        """식단 유료 상세 리포트 태스크를 큐에 등록하고 task_id를 반환한다."""
        task = _celery_sender.send_task(
            "vision.analyze_meal_paid",
            args=[image_base64, media_type, risk_factors],
        )
        return task.id

    # ── 운동 캡처 인증 (+100pt) ──

    @staticmethod
    def enqueue_exercise(image_base64: str, media_type: str) -> str:
        """운동 캡처 인증 태스크를 큐에 등록하고 task_id를 반환한다."""
        task = _celery_sender.send_task(
            "vision.analyze_exercise",
            args=[image_base64, media_type],
        )
        return task.id

    # ── 결과 조회 (공통) ──

    @staticmethod
    def get_task_result(task_id: str) -> dict:
        """Celery 태스크 상태 및 결과를 조회한다."""
        result = AsyncResult(task_id, app=_celery_result)

        if result.state == "PENDING":
            return {"task_id": task_id, "status": "PENDING", "result": None, "error": None}

        if result.state == "SUCCESS":
            return {"task_id": task_id, "status": "SUCCESS", "result": result.result, "error": None}

        if result.state == "FAILURE":
            return {"task_id": task_id, "status": "FAILURE", "result": None, "error": str(result.result)}

        # RETRY, STARTED 등 기타 상태
        return {"task_id": task_id, "status": result.state, "result": None, "error": None}
