from sqlalchemy.ext.asyncio import AsyncSession

from app.dtos.users import DashboardResponse, ProfileUpdateRequest
from app.models.users import User
from app.repositories.user_repository import UserRepository


class UserManageService:
    def __init__(self, session: AsyncSession):
        self.repo = UserRepository(session)

    async def update_profile(self, user: User, data: ProfileUpdateRequest) -> User:
        """닉네임 및 프로필 이미지를 수정한다."""
        await self.repo.update_instance(user=user, data=data.model_dump(exclude_none=True))
        return user

    async def withdraw_user(self, user: User) -> None:
        """사용자의 계정과 모든 관련 데이터를 영구적으로 삭제한다."""
        await self.repo.hard_delete_user(user)

    async def get_dashboard(self, user: User) -> DashboardResponse:
        """마이페이지 대시보드에 표시할 건강 현황 요약 정보를 반환한다."""
        return DashboardResponse.model_validate(user)
