import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.models.users import User
from app.repositories.user_repository import UserRepository
from app.services.google_oauth import GoogleOAuthService, GoogleUserInfo
from app.services.jwt import JwtService
from app.utils.jwt.tokens import AccessToken, RefreshToken

# 탈퇴 후 계정 복구 가능 기간
RESTORE_PERIOD_DAYS = 7

# __name__: 현재 모듈 경로(app.services.auth)를 로거 이름으로 사용
# 로그 출력 시 어떤 파일에서 발생한 로그인지 자동 식별 가능
logger = logging.getLogger(__name__)

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
        logger.info("소셜 로그인 요청 수신 - provider: %s", provider)

        if provider not in SUPPORTED_PROVIDERS:
            logger.warning("지원하지 않는 provider 요청: %s", provider)
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
        """Google ID 토큰으로 로그인/회원가입 처리"""
        google_oauth = GoogleOAuthService()

        logger.info("Google ID 토큰 검증 시작")
        token_data = await google_oauth.exchange_code(code)
        google_user: GoogleUserInfo = await google_oauth.get_user_info(token_data["access_token"])
        logger.info("Google ID 토큰 검증 성공")


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
            logger.info("신규 사용자 생성 완료 - user_id: %d", user.id)
        else:
            logger.info("기존 사용자 로그인 - user_id: %d", user.id)

        if user.is_deleted:
            is_new_user = await self._handle_withdrawn_user(user, google_user.name)

        tokens = self.jwt_service.issue_jwt_pair(user)
        logger.info("JWT 토큰 발급 완료 - user_id: %d, is_new_user: %s", user.id, is_new_user)
        return LoginResult(tokens=tokens, user=user, is_new_user=is_new_user)

    async def _handle_withdrawn_user(self, user: User, google_name: str) -> bool:
        """
        탈퇴한 사용자의 재로그인 처리.

        - 탈퇴 후 7일 이내: 계정 복구 (기존 데이터 유지, is_new_user=False)
        - 탈퇴 후 7일 초과: 프로필 완전 초기화 (is_new_user=True → 초기 프로필 설정 필요)

        Returns:
            is_new_user (bool): 프론트엔드가 초기 프로필 설정 화면으로 안내할지 여부
        """
        if user.deleted_at is None:
            # deleted_at이 없는 비정상 상태 → 복구 처리
            logger.warning("deleted_at 누락된 탈퇴 계정 복구 - user_id: %d", user.id)
            await self.user_repo.restore_user(user)
            return False

        restore_deadline = user.deleted_at + timedelta(days=RESTORE_PERIOD_DAYS)
        is_restorable = datetime.now() <= restore_deadline

        if is_restorable:
            # 7일 이내: 기존 데이터 유지하며 계정 복구
            logger.info(
                "계정 복구 처리 - user_id: %d, deleted_at: %s, deadline: %s",
                user.id, user.deleted_at, restore_deadline,
            )
            await self.user_repo.restore_user(user)
            return False
        else:
            # 7일 초과: 프로필 초기화 후 신규 사용자로 처리
            logger.info(
                "계정 초기화 처리 - user_id: %d, deleted_at: %s (7일 초과)",
                user.id, user.deleted_at,
            )
            await self.user_repo.reset_user(user, nickname=google_name[:20])
            return True
