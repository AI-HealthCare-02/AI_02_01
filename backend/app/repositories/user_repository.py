from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._model = User

    async def get_user(self, user_id: int) -> User | None:
        result = await self._session.execute(
            select(self._model).where(self._model.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_provider_id(self, provider: str, provider_id: str) -> User | None:
        result = await self._session.execute(
            select(self._model).where(
                self._model.provider == provider,
                self._model.provider_id == provider_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_oauth_user(self, provider: str, provider_id: str, nickname: str) -> User:
        user = self._model(
            provider=provider,
            provider_id=provider_id,
            nickname=nickname,
        )
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def update_instance(self, user: User, data: dict[str, Any]) -> None:
        for key, value in data.items():
            if value is not None:
                setattr(user, key, value)
        await self._session.commit()
        await self._session.refresh(user)
