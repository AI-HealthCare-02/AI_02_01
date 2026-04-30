from pydantic import BaseModel

from app.dtos.base import BaseSerializerModel

# ──────────────────────────────────────────────
# Request DTOs
# ──────────────────────────────────────────────

class SocialLoginRequest(BaseModel):
    code: str


# ──────────────────────────────────────────────
# Response DTOs
# ──────────────────────────────────────────────

class LoginUserResponse(BaseSerializerModel):
    """로그인 응답에 포함될 사용자 정보"""
    id: int
    email: str | None
    provider: str
    provider_id: str
    nickname: str
    role: str
    character_stage: int
    current_point: int


class SocialLoginResponse(BaseModel):
    """소셜 로그인/회원가입 통합 응답"""
    is_new_user: bool
    access_token: str
    user: LoginUserResponse


class TokenRefreshResponse(BaseModel):
    access_token: str


# ──────────────────────────────────────────────
# Error Response DTOs (Swagger 문서 표시용)
# ──────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """에러 응답 공통 형식"""
    detail: str
