"""
ML2 Vision API DTO (Request/Response 스키마)

위치: backend/app/dtos/ai_vision.py
역할: 식단 분석 / 운동 캡처 인증 엔드포인트의 입출력 형식 정의
"""

from pydantic import BaseModel, Field
from typing import Optional, Any


# ══════════════════════════════════════════════
# 공통 응답
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
    result: Optional[Any] = Field(default=None, description="태스크 결과 (완료 시)")
    error: Optional[str] = Field(default=None, description="에러 메시지 (실패 시)")


class ErrorResponse(BaseModel):
    """에러 응답"""
    detail: str


# ══════════════════════════════════════════════
# 식단 분석 요청
# ══════════════════════════════════════════════

class MealAnalyzeRequest(BaseModel):
    """식단 분석 요청 (무료/유료 공용)"""
    image_base64: str = Field(..., description="이미지 base64 인코딩 문자열")
    media_type: str = Field(
        default="image/jpeg",
        description="이미지 MIME 타입 (image/jpeg, image/png, image/webp, image/gif)",
    )
    risk_factors: str = Field(
        default="",
        description="사용자 위험 요인 (예: '고혈압, 당뇨')",
    )


# ══════════════════════════════════════════════
# 운동 캡처 인증 요청
# ══════════════════════════════════════════════

class ExerciseAnalyzeRequest(BaseModel):
    """운동 앱 스크린샷 인증 요청"""
    image_base64: str = Field(..., description="운동 앱 스크린샷 base64 인코딩 문자열")
    media_type: str = Field(
        default="image/jpeg",
        description="이미지 MIME 타입",
    )
