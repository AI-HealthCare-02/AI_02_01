from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.repositories.user_repository import UserRepository
from app.services.google_oauth import GoogleUserInfo
from app.services.jwt import JwtService
from app.utils.jwt.tokens import AccessToken, RefreshToken


class AuthService:
    def __init__(self, session: AsyncSession):
        self.user_repo = UserRepository(session)
        self.jwt_service = JwtService()

    async def google_login(self, google_user: GoogleUserInfo) -> tuple[dict[str, AccessToken | RefreshToken], bool]:
        user = await self.user_repo.get_user_by_provider_id("google", google_user.sub)
        is_new_user = False

        if not user:
            is_new_user = True
            user = await self.user_repo.create_oauth_user(
                provider="google",
                provider_id=google_user.sub,
                nickname=google_user.name[:20],
            )

        if user.is_deleted:
            raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="비활성화된 계정입니다.")

        tokens = self.jwt_service.issue_jwt_pair(user)
        return tokens, is_new_user
