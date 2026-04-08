from pydantic import BaseModel

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
