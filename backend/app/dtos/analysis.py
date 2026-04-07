from typing import Annotated, Self

from pydantic import BaseModel, Field, model_validator

from app.dtos.health import HealthRecordCreateRequest

# ──────────────────────────────────────────────
# Request DTOs
# ──────────────────────────────────────────────


class HealthAnalysisRequest(BaseModel):
    """
    AI 건강 분석 요청.
    record_id(기존 기록) 또는 health_data(새 데이터) 중 하나 필수.
    """

    record_id: Annotated[int | None, Field(None, description="분석할 건강검진 기록 ID (기존 기록 기반)")] = None
    health_data: Annotated[
        HealthRecordCreateRequest | None, Field(None, description="분석할 건강검진 수치 (새 데이터 기반)")
    ] = None

    @model_validator(mode="after")
    def check_exactly_one(self) -> Self:
        """record_id와 health_data 중 정확히 하나만 존재해야 함"""
        has_record = self.record_id is not None
        has_data = self.health_data is not None
        if has_record == has_data:
            raise ValueError("record_id 또는 health_data 중 하나만 입력해야 합니다.")
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
