"""
FirstCare Vision Service
GPT Vision API 기반 식단 분석 + 운동 캡처 인증

사용법:
    from ai.services.vision import MealService, ExerciseService

    meal_svc = MealService()
    result = await meal_svc.analyze_free(image_bytes, "image/jpeg")
"""

from .meal_service import MealService
from .exercise_service import ExerciseService
from .checkup_service import CheckupService

__all__ = ["MealService", "ExerciseService", "CheckupService"]
