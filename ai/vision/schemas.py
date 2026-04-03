"""
Vision API Response Schemas
Pydantic 모델로 타입 안전성 확보
FastAPI 라우터에서 response_model로 사용

노트북(vision_api_test.ipynb) 최신 JSON 스키마와 1:1 매핑
"""

from typing import Literal
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# 공통
# ──────────────────────────────────────────────
class NutritionRatio(BaseModel):
    carbohydrate_pct: int = Field(ge=0, le=100, description="탄수화물 비율 (%)")
    protein_pct: int = Field(ge=0, le=100, description="단백질 비율 (%)")
    fat_pct: int = Field(ge=0, le=100, description="지방 비율 (%)")


class UsageInfo(BaseModel):
    prompt_tokens: int = Field(ge=0, description="프롬프트 토큰 수")
    completion_tokens: int = Field(ge=0, description="생성 토큰 수")
    total_tokens: int = Field(ge=0, description="총 토큰 수")
    estimated_cost: float = Field(ge=0, description="예상 비용")


# ──────────────────────────────────────────────
# 식단 분석 — 무료
# ──────────────────────────────────────────────
class MealFreeResult(BaseModel):
    food_name: str = Field(min_length=1, description="대표 음식명")
    food_items: list[str] = Field(description="구성 음식 목록")
    nutrition_ratio: NutritionRatio
    sodium_level: Literal["높음", "보통", "낮음"] = Field(description="나트륨 수준")
    feedback: str = Field(min_length=1, description="한 줄 피드백")


class MealFreeResponse(BaseModel):
    result: MealFreeResult
    usage: UsageInfo


# ──────────────────────────────────────────────
# 식단 분석 — 유료 상세 리포트
# ──────────────────────────────────────────────
class DetailedAnalysis(BaseModel):
    strength: str = Field(min_length=1, description="강점 분석")
    improvement: str = Field(min_length=1, description="개선 포인트")


class VitaminInfo(BaseModel):
    level: Literal["높음", "보통", "낮음"] = Field(description="비타민 수준")
    detail: str = Field(min_length=1, description="주요 비타민 설명 (1문장)")


class MineralInfo(BaseModel):
    level: Literal["높음", "보통", "낮음"] = Field(description="무기질 수준")
    detail: str = Field(min_length=1, description="주요 무기질 설명 (1문장)")


class NutrientRecommendation(BaseModel):
    nutrient: str = Field(min_length=1, description="추천 영양소")
    foods: list[str] = Field(description="추천 음식 목록")
    reason: str = Field(min_length=1, description="추천 이유")


class NextMealSuggestion(BaseModel):
    concept: str = Field(min_length=1, description="다음 끼니 컨셉")
    menu_example: list[str] = Field(description="예시 메뉴")
    reason: str = Field(min_length=1, description="추천 이유")


class MealPaidResult(BaseModel):
    food_name: str = Field(min_length=1, description="대표 음식명")
    food_items: list[str] = Field(description="구성 음식 목록")
    estimated_calories: int = Field(ge=0, description="추정 칼로리 (kcal)")
    nutrition_ratio: NutritionRatio
    sodium_level: Literal["높음", "보통", "낮음"] = Field(description="나트륨 수준")
    vitamin_info: VitaminInfo
    mineral_info: MineralInfo
    detailed_analysis: DetailedAnalysis
    recommendations: list[NutrientRecommendation] = Field(description="보충 추천 영양소 목록")
    next_meal_suggestion: NextMealSuggestion
    overall_score: int = Field(ge=1, le=10, description="종합 점수")
    feedback_summary: str = Field(min_length=1, description="종합 요약")


class MealPaidResponse(BaseModel):
    result: MealPaidResult
    usage: UsageInfo


# ──────────────────────────────────────────────
# 운동 캡처 OCR
# ──────────────────────────────────────────────
class ExerciseMetrics(BaseModel):
    steps: int | None = Field(default=None, ge=0, description="걸음 수")
    distance_km: float | None = Field(default=None, ge=0, description="이동 거리(km)")
    duration_minutes: float | None = Field(default=None, ge=0, description="운동 시간(분)")
    calories_burned: int | None = Field(default=None, ge=0, description="소모 칼로리(kcal)")


class ExerciseResult(BaseModel):
    exercise_type: str = Field(min_length=1, description="운동 종류")
    metrics: ExerciseMetrics
    is_verified: bool = Field(description="인증 가능 여부")
    confidence: Literal["high", "medium", "low"] = Field(description="분석 신뢰도")
    note: str | None = Field(default=None, description="보조 설명")


class ExerciseResponse(BaseModel):
    result: ExerciseResult
    usage: UsageInfo