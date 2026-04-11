from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, Field, computed_field, model_validator

# ──────────────────────────────────────────────
# Request DTOs
# ──────────────────────────────────────────────


class GuestAnalysisRequest(BaseModel):
    """비회원 AI 건강 분석 요청 (DB 기록 없이 직접 수치 입력)"""

    birth_date: Annotated[
        date,
        Field(description="생년월일 (YYYY-MM-DD). 만 나이는 자동 계산됨."),
    ]
    gender: Annotated[Literal["M", "F"], Field(description="성별 (M: 남성, F: 여성)")]
    height: Annotated[float, Field(ge=100, le=300, description="키 (cm)")]
    weight: Annotated[float, Field(ge=10, le=500, description="몸무게 (kg)")]
    systolic_bp: Annotated[int, Field(ge=50, le=300, description="수축기 혈압 (mmHg)")]
    diastolic_bp: Annotated[int, Field(ge=30, le=200, description="이완기 혈압 (mmHg)")]
    total_cholesterol: Annotated[int, Field(ge=50, le=500, description="총 콜레스테롤 (mg/dL)")]
    glucose: Annotated[int, Field(ge=30, le=600, description="공복 혈당 (mg/dL)")]
    smoke_yn: Annotated[bool, Field(description="흡연 여부")]
    alcohol_yn: Annotated[bool, Field(description="음주 여부")]
    exercise_yn: Annotated[bool, Field(description="규칙적 운동 여부")]

    @computed_field
    @property
    def age(self) -> int:
        """생년월일 기반 만 나이 자동 계산 (요청 시점 기준)"""
        today = date.today()
        age = today.year - self.birth_date.year
        # 올해 생일이 아직 지나지 않았으면 1 감산
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            age -= 1
        return age

    @model_validator(mode="after")
    def validate_birth_date(self) -> "GuestAnalysisRequest":
        """생년월일 유효성 검증 (미래 날짜 / 나이 범위 초과 차단)"""
        today = date.today()

        if self.birth_date > today:
            raise ValueError("생년월일은 오늘 이후일 수 없습니다.")

        if self.age < 1:
            raise ValueError("나이는 최소 1세 이상이어야 합니다.")

        if self.age > 120:
            raise ValueError("유효하지 않은 생년월일입니다. (120세 초과)")

        return self


# ──────────────────────────────────────────────
# Response DTOs
# ──────────────────────────────────────────────


class AnalysisTaskResponse(BaseModel):
    """AI 분석 작업 제출 응답 (비동기 - Celery task 제출됨)"""

    task_id: str
    status: str = "pending"


class AnalysisResultResponse(BaseModel):
    """AI 분석 결과 조회 응답 (캐시 히트 시 즉시 반환 / task 완료 후 반환)"""

    status: str  # "pending" | "success" | "failed"
    data: dict | None = None  # {"ml1_predict": {...}, "ml1_comment": {...}}
    error: str | None = None
