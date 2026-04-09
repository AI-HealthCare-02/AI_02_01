import logging
from datetime import datetime

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
        age는 birth_year 기반 자동 계산.
        """
        if user.gender is not None:
            logger.warning("초기 프로필 재설정 시도 - user_id: %d", user.id)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="초기 프로필이 이미 설정되어 있습니다. 성별은 변경할 수 없습니다.",
            )

        update_data = {
            "gender": data.gender,
            "birth_year": data.birth_year,
            "age": self._calculate_age(data.birth_year),
        }
        if data.nickname is not None:
            update_data["nickname"] = data.nickname

        await self.repo.update_instance(user=user, data=update_data)
        logger.info(
            "초기 프로필 설정 완료 - user_id: %d, gender: %s, birth_year: %d", user.id, data.gender, data.birth_year
        )
        return user

    async def update_profile(self, user: User, data: ProfileUpdateRequest) -> User:
        """닉네임, 프로필 이미지, 출생 연도를 수정한다. birth_year 변경 시 age 자동 재계산."""
        update_data = data.model_dump(exclude_none=True)

        # birth_year 변경 시 age 자동 재계산
        if "birth_year" in update_data:
            update_data["age"] = self._calculate_age(update_data["birth_year"])

        await self.repo.update_instance(user=user, data=update_data)
        return user

    async def withdraw_user(self, user: User) -> None:
        """사용자의 계정과 모든 관련 데이터를 영구적으로 삭제한다."""
        await self.repo.hard_delete_user(user)

    async def get_dashboard(self, user: User) -> DashboardResponse:
        """마이페이지 대시보드에 표시할 건강 현황 요약 정보를 반환한다."""
        return DashboardResponse.model_validate(user)

    @staticmethod
    def _calculate_age(birth_year: int) -> int:
        """출생 연도 기반 나이 계산 (현재 연도 - 출생 연도 + 1)"""
        return datetime.now().year - birth_year + 1
