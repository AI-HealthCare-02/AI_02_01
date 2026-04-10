"""
ML2 Vision API DTO (Request/Response 스키마)

위치: backend/app/dtos/ai_vision.py
역할: 식단 분석 / 운동 캡처 인증 엔드포인트의 입출력 형식 정의

요청 방식: multipart/form-data (UploadFile + Form)
- 요청 DTO는 라우터에서 File()/Form() 파라미터로 직접 처리
- 응답 DTO만 Pydantic BaseModel 사용
"""

from typing import Any

from pydantic import BaseModel, Field

# ══════════════════════════════════════════════
# 응답 DTO
# ══════════════════════════════════════════════


class TaskResponse(BaseModel):
    """Celery 태스크 접수 응답"""

    task_id: str = Field(..., description="Celery 태스크 ID (결과 조회용)")
    status: str = Field(default="PENDING", description="태스크 상태")
    message: str = Field(..., description="안내 메시지")


class TaskResultResponse(BaseModel):
    """Celery 태스크 결과 조회 응답"""

    task_id: str
    status: str = Field(..., description="PENDING | SUCCESS | FAILURE")
    result: Any | None = Field(default=None, description="태스크 결과 (완료 시)")
    error: str | None = Field(default=None, description="에러 메시지 (실패 시)")


class ErrorResponse(BaseModel):
    """에러 응답"""

    detail: str
