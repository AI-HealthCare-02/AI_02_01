from sqlalchemy.ext.asyncio import AsyncSession

from app.dtos.users import UserUpdateRequest
from app.models.users import User
from app.repositories.user_repository import UserRepository


class UserManageService:
    def __init__(self, session: AsyncSession):
        self.repo = UserRepository(session)

    async def update_user(self, user: User, data: UserUpdateRequest) -> User:
        await self.repo.update_instance(user=user, data=data.model_dump(exclude_none=True))
        return user
