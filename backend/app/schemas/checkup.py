from typing import Literal

from pydantic import BaseModel, Field


class UsageInfo(BaseModel):
    prompt_tokens: int = Field(ge=0, description="프롬프트 토큰 수")
    completion_tokens: int = Field(ge=0, description="생성 토큰 수")
    total_tokens: int = Field(ge=0, description="총 토큰 수")
    estimated_cost: float = Field(ge=0, description="예상 비용")


class CheckupResult(BaseModel):
    birth_year: int | None = Field(default=None, ge=1900, le=2100, description="출생연도")
    gender: Literal["M", "F"] | None = Field(default=None, description="성별 (M/F)")
    height: float | None = Field(default=None, ge=0, description="신장 (cm)")
    weight: float | None = Field(default=None, ge=0, description="체중 (kg)")
    systolic_bp: int | None = Field(default=None, ge=0, description="수축기 혈압 (mmHg)")
    diastolic_bp: int | None = Field(default=None, ge=0, description="이완기 혈압 (mmHg)")
    glucose: int | None = Field(default=None, ge=0, description="공복혈당 (mg/dL)")
    total_cholesterol: int | None = Field(default=None, ge=0, description="총콜레스테롤 (mg/dL)")
    is_valid: bool = Field(description="건강검진 결과지 여부")
    confidence: Literal["high", "medium", "low"] = Field(description="분석 신뢰도")
    note: str | None = Field(default=None, description="보조 설명")


class CheckupResponse(BaseModel):
    result: CheckupResult
    usage: UsageInfo
