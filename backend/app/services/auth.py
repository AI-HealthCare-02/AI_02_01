from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.models.users import User
from app.repositories.user_repository import UserRepository
from app.services.google_oauth import GoogleOAuthService, GoogleUserInfo
from app.services.jwt import JwtService
from app.utils.jwt.tokens import AccessToken, RefreshToken

SUPPORTED_PROVIDERS = {"google"}


@dataclass
class LoginResult:
    """로그인 처리 결과를 담는 데이터 클래스"""
    tokens: dict[str, AccessToken | RefreshToken]
    user: User
    is_new_user: bool


class AuthService:
    def __init__(self, session: AsyncSession):
        self.user_repo = UserRepository(session)
        self.jwt_service = JwtService()

    async def social_login(self, provider: str, code: str) -> LoginResult:
        """
        소셜 로그인 통합 처리: provider에 따라 분기
        - 지원하지 않는 provider → 400 Bad Request
        - 인가 코드 무효 → 400 Bad Request (GoogleOAuthService에서 발생)
        - Google 서버 오류 → 502 Bad Gateway (GoogleOAuthService에서 발생)
        - 비활성화된 계정 → 423 Locked
        """
        if provider not in SUPPORTED_PROVIDERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"지원하지 않는 로그인 제공자입니다: {provider}",
            )

        if provider == "google":
            return await self._google_login(code)

        # 향후 kakao, naver 등 추가 시 여기에 분기
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"지원하지 않는 로그인 제공자입니다: {provider}",
        )

    async def _google_login(self, code: str) -> LoginResult:
        """Google OAuth 인가 코드로 로그인/회원가입 처리"""
        google_oauth = GoogleOAuthService()
        token_data = await google_oauth.exchange_code(code)
        google_user: GoogleUserInfo = await google_oauth.get_user_info(token_data["access_token"])

        user = await self.user_repo.get_user_by_provider_id("google", google_user.sub)
        is_new_user = False

        if not user:
            is_new_user = True
            user = await self.user_repo.create_oauth_user(
                provider="google",
                provider_id=google_user.sub,
                nickname=google_user.name[:20],
                email=google_user.email,
            )

        if user.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="비활성화된 계정입니다.",
            )

        tokens = self.jwt_service.issue_jwt_pair(user)
        return LoginResult(tokens=tokens, user=user, is_new_user=is_new_user)
