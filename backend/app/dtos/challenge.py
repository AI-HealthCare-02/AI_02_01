from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.models.challenges import VerificationMethodEnum

# ──────────────────────────────────────────────
# Request DTOs
# ──────────────────────────────────────────────


class ChallengeLogRequest(BaseModel):
    """챌린지 인증 요청"""

    verification_type: VerificationMethodEnum = Field(
        ...,
        description="인증 방식: checklist / input / cv",
        examples=["checklist"],
    )
    input_value: str | None = Field(
        default=None,
        description="수치 입력값 (input 방식일 때만 사용, 예: 흡연 개피수)",
        examples=["3"],
    )
    cv_result_id: int | None = Field(
        default=None,
        description="CV 분석 결과 ID (cv 방식일 때만 사용)",
    )

    @model_validator(mode="after")
    def check_required_fields(self):
        if self.verification_type == VerificationMethodEnum.INPUT and self.input_value is None:
            raise ValueError("input 방식은 input_value가 필요합니다.")
        if self.verification_type == VerificationMethodEnum.CV and self.cv_result_id is None:
            raise ValueError("cv 방식은 cv_result_id가 필요합니다.")
        if self.verification_type == VerificationMethodEnum.CHECKLIST:
            if self.input_value is not None or self.cv_result_id is not None:
                raise ValueError("checklist 방식은 input_value, cv_result_id를 사용하지 않습니다.")
        return self


# ──────────────────────────────────────────────
# Response DTOs
# ──────────────────────────────────────────────


class ChallengeResponse(BaseModel):
    """챌린지 풀 단건 응답"""

    id: int
    category: str
    title: str
    description: str | None = None
    expected_effect: str | None = None
    verification_method: str
    target_risk_factors: str | None = None
    duration_days: int
    required_success_days: int


class ChallengeListResponse(BaseModel):
    """챌린지 목록 응답"""

    challenges: list[ChallengeResponse]


class UserChallengeResponse(BaseModel):
    """사용자 챌린지 참여 응답"""

    id: int
    user_id: int
    challenge_id: int
    status: str
    current_streak: int
    start_date: date
    completed_at: datetime | None = None


class ChallengeLogResponse(BaseModel):
    """챌린지 인증 응답"""

    id: int
    user_challenge_id: int
    log_date: date
    verification_type: str
    input_value: str | None = None
    cv_result_id: int | None = None
    created_at: datetime
    current_streak: int
    is_completed: bool


class MessageResponse(BaseModel):
    """단순 메시지 응답 (포기 등)"""

    message: str


# ──────────────────────────────────────────────
# Error Response DTOs (Swagger 문서 표시용)
# ──────────────────────────────────────────────


class ErrorResponse(BaseModel):
    """에러 응답 공통 형식"""

    detail: str


class MyActiveChallengeResponse(BaseModel):
    """내 진행 중인 챌린지 단건"""

    user_challenge_id: int
    challenge_id: int
    title: str
    category: str
    current_streak: int
    start_date: date
    duration_days: int
    required_success_days: int
    verification_method: str


class MyActiveChallengeListResponse(BaseModel):
    """내 진행 중인 챌린지 목록"""

    challenges: list[MyActiveChallengeResponse]


class ChallengeRecommendItem(BaseModel):
    """AI 추천 챌린지 단건"""

    challenge_id: int
    title: str
    reason: str


class ChallengeRecommendResponse(BaseModel):
    """AI 챌린지 추천 응답"""

    recommendations: list[ChallengeRecommendItem]
