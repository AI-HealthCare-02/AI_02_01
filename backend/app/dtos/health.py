from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from app.dtos.base import BaseSerializerModel

# ──────────────────────────────────────────────
# Request DTOs
# ──────────────────────────────────────────────


class HealthRecordCreateRequest(BaseModel):
    """건강검진 수치 신규 입력 요청 (user_id는 인증 토큰에서 추출, bmi는 서버 자동 계산)"""

    systolic_bp: Annotated[int, Field(ge=50, le=300, description="수축기 혈압 (mmHg)")]
    diastolic_bp: Annotated[int, Field(ge=30, le=200, description="이완기 혈압 (mmHg)")]
    total_cholesterol: Annotated[int, Field(ge=50, le=500, description="총 콜레스테롤 (mg/dL)")]
    glucose: Annotated[int, Field(ge=30, le=600, description="혈당 (mg/dL)")]
    height: Annotated[float, Field(ge=100, le=300, description="키 (cm) - 100cm 이상 입력 필요")]
    weight: Annotated[float, Field(ge=10, le=500, description="몸무게 (kg)")]
    smoke_yn: Annotated[bool, Field(description="흡연 여부")]
    alcohol_yn: Annotated[bool, Field(description="음주 여부")]
    exercise_yn: Annotated[bool, Field(description="규칙적 운동 여부")]


class HealthRecordUpdateRequest(BaseModel):
    """건강검진 수치 수정 요청 (PATCH - None인 필드는 수정하지 않음)"""

    systolic_bp: Annotated[int | None, Field(None, ge=50, le=300, description="수축기 혈압 (mmHg)")]
    diastolic_bp: Annotated[int | None, Field(None, ge=30, le=200, description="이완기 혈압 (mmHg)")]
    total_cholesterol: Annotated[int | None, Field(None, ge=50, le=500, description="총 콜레스테롤 (mg/dL)")]
    glucose: Annotated[int | None, Field(None, ge=30, le=600, description="혈당 (mg/dL)")]
    height: Annotated[float | None, Field(None, ge=100, le=300, description="키 (cm) - 100cm 이상 입력 필요")]
    weight: Annotated[float | None, Field(None, ge=10, le=500, description="몸무게 (kg)")]
    smoke_yn: Annotated[bool | None, Field(None, description="흡연 여부")]
    alcohol_yn: Annotated[bool | None, Field(None, description="음주 여부")]
    exercise_yn: Annotated[bool | None, Field(None, description="규칙적 운동 여부")]


# ──────────────────────────────────────────────
# Response DTOs
# ──────────────────────────────────────────────


class HealthRecordResponse(BaseSerializerModel):
    """건강검진 기록 단건 응답"""

    id: int
    user_id: int | None
    systolic_bp: int
    diastolic_bp: int
    total_cholesterol: int
    glucose: int
    height: float
    weight: float
    bmi: float | None
    smoke_yn: bool
    alcohol_yn: bool
    exercise_yn: bool
    created_at: datetime


class HealthRecordListResponse(BaseModel):
    """건강검진 기록 목록 응답"""

    records: list[HealthRecordResponse]
