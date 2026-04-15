import logging

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.dtos.users import DashboardResponse, InitialProfileRequest, ProfileUpdateRequest
from app.models.users import User
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class UserManageService:
    def __init__(self, session: AsyncSession):
        self.repo = UserRepository(session)

    async def setup_initial_profile(self, user: User, data: InitialProfileRequest) -> User:
        """
        초기 프로필 설정 (Google 로그인 직후 1회).
        gender 이미 설정된 경우 409 Conflict 반환.
        age는 birth_year hybrid_property로 동적 계산되므로 DB에 저장하지 않는다.
        """
        if user.gender is not None:
            logger.warning("초기 프로필 재설정 시도 - user_id: %d", user.id)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="초기 프로필이 이미 설정되어 있습니다. 성별은 변경할 수 없습니다.",
            )

        update_data: dict = {
            "gender": data.gender,
            "birth_year": data.birth_year,
        }
        if data.nickname is not None:
            update_data["nickname"] = data.nickname

        await self.repo.update_instance(user=user, data=update_data)
        logger.info(
            "초기 프로필 설정 완료 - user_id: %d, gender: %s, birth_year: %d", user.id, data.gender, data.birth_year
        )
        return user

    async def update_profile(self, user: User, data: ProfileUpdateRequest) -> User:
        """닉네임, 프로필 이미지, 출생 연도를 수정한다. age는 birth_year 기반 동적 계산이므로 별도 저장 불필요."""
        update_data = data.model_dump(exclude_none=True)
        await self.repo.update_instance(user=user, data=update_data)
        return user

    async def withdraw_user(self, user: User, reason: str | None = None) -> None:
        """
        사용자 탈퇴 처리 (Soft Delete).
        is_deleted=True, deleted_at=현재 시각으로 마킹하며 실제 레코드는 유지된다.
        탈퇴 사유는 선택 입력이며 withdraw_reason 컬럼에 저장된다.
        이후 인증 시 get_request_user에서 자동으로 접근이 차단된다.
        """
        await self.repo.soft_delete_user(user, reason=reason)

    async def get_dashboard(self, user: User) -> DashboardResponse:
        """마이페이지 대시보드에 표시할 건강 현황 요약 정보를 반환한다."""
        return DashboardResponse.model_validate(user)
