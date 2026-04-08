"""
ML2 Vision API Service — Celery 태스크 호출 및 결과 조회

위치: backend/app/services/ai_vision_service.py
역할: 라우터에서 받은 데이터 → Celery ml2 큐에 태스크 등록 → task_id 반환

현재: dummy task로 파이프라인 테스트
나중에: ai.vision.tasks import로 한 줄 교체
"""

from celery.result import AsyncResult
from celery import Celery
import os

# ──────────────────────────────────────────────
# Celery 앱
# ──────────────────────────────────────────────
# 현재: 로컬 테스트용 celery 앱
# 나중에: from ai.celery_app import celery_app

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "ai_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
)


# ──────────────────────────────────────────────
# Dummy Tasks (파이프라인 테스트용)
# ──────────────────────────────────────────────
# 실제 교체 시 이 블록 전체 삭제하고 아래 import 활성화:
#
#   from ai.vision.tasks import (
#       analyze_meal_free,
#       analyze_meal_paid,
#       analyze_exercise,
#   )

@celery_app.task(name="dummy.meal_free", queue="ml2")
def dummy_meal_free(image_base64: str, media_type: str, risk_factors: str = ""):
    return {
        "status": "success",
        "task_name": "식단_무료_분석",
        "data": {
            "result": {
                "food_name": "더미 음식",
                "calories": 500,
                "score": 7,
                "feedback": "더미 응답입니다. Vision API 연결 후 교체됩니다.",
            },
            "usage": {"model": "dummy", "tokens": 0},
        },
        "error": None,
    }


@celery_app.task(name="dummy.meal_paid", queue="ml2")
def dummy_meal_paid(image_base64: str, media_type: str, risk_factors: str = ""):
    return {
        "status": "success",
        "task_name": "식단_유료_분석",
        "data": {
            "result": {
                "food_name": "더미 음식",
                "calories": 500,
                "score": 7,
                "feedback": "더미 상세 리포트입니다.",
                "vitamin_info": "비타민 정보 더미",
                "mineral_info": "미네랄 정보 더미",
                "sodium_level": "보통",
            },
            "usage": {"model": "dummy", "tokens": 0},
        },
        "error": None,
    }


@celery_app.task(name="dummy.exercise", queue="ml2")
def dummy_exercise(image_base64: str, media_type: str):
    return {
        "status": "success",
        "task_name": "운동_캡처_인증",
        "data": {
            "result": {
                "is_valid": True,
                "exercise_type": "러닝",
                "duration_minutes": 30,
                "feedback": "더미 운동 인증 결과입니다.",
            },
        },
        "error": None,
    }


# ══════════════════════════════════════════════
# Service 클래스
# ══════════════════════════════════════════════

class AIVisionService:
    """
    ML2 Vision API Celery 태스크 호출 서비스

    교체 가이드:
        dummy_meal_free.delay(...)  →  analyze_meal_free.delay(...)
        dummy_meal_paid.delay(...)  →  analyze_meal_paid.delay(...)
        dummy_exercise.delay(...)   →  analyze_exercise.delay(...)
    """

    # ── 식단 무료 분석 (+100pt) ──

    @staticmethod
    def enqueue_meal_free(image_base64: str, media_type: str, risk_factors: str = "") -> str:
        task = dummy_meal_free.delay(image_base64, media_type, risk_factors)
        return task.id

    # ── 식단 유료 리포트 (-300pt) ──

    @staticmethod
    def enqueue_meal_paid(image_base64: str, media_type: str, risk_factors: str = "") -> str:
        task = dummy_meal_paid.delay(image_base64, media_type, risk_factors)
        return task.id

    # ── 운동 캡처 인증 (+100pt) ──

    @staticmethod
    def enqueue_exercise(image_base64: str, media_type: str) -> str:
        task = dummy_exercise.delay(image_base64, media_type)
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
