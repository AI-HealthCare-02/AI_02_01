"""
ML2 Vision API Service — Celery 태스크 호출 및 결과 조회

위치: backend/app/services/ai_vision_service.py
역할: 라우터에서 받은 데이터 → Celery ml2 큐에 태스크 등록 → task_id 반환
"""

from celery.result import AsyncResult

# ──────────────────────────────────────────────
# 공통 Celery 앱 + 실제 Vision 태스크
# ──────────────────────────────────────────────
from ai.celery_app import celery_app
from ai.vision.tasks import (
    analyze_meal_free,
    analyze_meal_paid,
    analyze_exercise,
)


# ══════════════════════════════════════════════
# Service 클래스
# ══════════════════════════════════════════════

class AIVisionService:
    """ML2 Vision API Celery 태스크 호출 서비스"""

    # ── 식단 무료 분석 (+100pt) ──

    @staticmethod
    def enqueue_meal_free(image_base64: str, media_type: str, risk_factors: str = "") -> str:
        task = analyze_meal_free.delay(image_base64, media_type, risk_factors)
        return task.id

    # ── 식단 유료 리포트 (-300pt) ──

    @staticmethod
    def enqueue_meal_paid(image_base64: str, media_type: str, risk_factors: str = "") -> str:
        task = analyze_meal_paid.delay(image_base64, media_type, risk_factors)
        return task.id

    # ── 운동 캡처 인증 (+100pt) ──

    @staticmethod
    def enqueue_exercise(image_base64: str, media_type: str) -> str:
        task = analyze_exercise.delay(image_base64, media_type)
        return task.id

    # ── 결과 조회 (공통) ──

    @staticmethod
    def get_task_result(task_id: str) -> dict:
        result = AsyncResult(task_id, app=celery_app)

        if result.state == "PENDING":
            return {
                "task_id": task_id,
                "status": "PENDING",
                "result": None,
                "error": None,
            }
        elif result.state == "SUCCESS":
            return {
                "task_id": task_id,
                "status": "SUCCESS",
                "result": result.result,
                "error": None,
            }
        elif result.state == "FAILURE":
            return {
                "task_id": task_id,
                "status": "FAILURE",
                "result": None,
                "error": str(result.result),
            }
        else:
            return {
                "task_id": task_id,
                "status": result.state,
                "result": None,
                "error": None,
            }