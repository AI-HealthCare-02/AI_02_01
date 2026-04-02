from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User


class UserRepository:
    """
    User 테이블에 대한 DB CRUD를 담당하는 레포지토리 클래스.
    서비스 계층(services/)에서 호출되며, SQLAlchemy AsyncSession을 통해 DB와 통신한다.
    """

    def __init__(self, session: AsyncSession):
        # 외부에서 주입받은 DB 세션 (FastAPI의 Depends를 통해 전달됨)
        self._session = session
        self._model = User

    async def get_user(self, user_id: int) -> User | None:
        """
        사용자 ID(PK)로 단일 사용자를 조회한다. 
        없으면 None 반환.
        """
        result = await self._session.execute(
            select(self._model).where(self._model.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_provider_id(self, provider: str, provider_id: str) -> User | None:
        """
        소셜 로그인 제공자(provider)와 제공자 고유 ID로 사용자를 조회한다.
        Google OAuth 로그인 시 기존 가입 여부를 확인하는 데 사용된다.
        """
        result = await self._session.execute(
            select(self._model).where(
                self._model.provider == provider,
                self._model.provider_id == provider_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_oauth_user(
        self, provider: str, provider_id: str, nickname: str, email: str | None = None
    ) -> User:
        """
        신규 OAuth 사용자를 생성하고 DB에 저장한다.
        commit 후 refresh하여 DB에서 자동 생성된 값(id, created_at 등)을 반영한다.
        """
        user = self._model(
            provider=provider,
            provider_id=provider_id,
            nickname=nickname,
            email=email,
        )
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def update_instance(self, user: User, data: dict[str, Any]) -> None:
        """
        전달받은 dict 데이터로 사용자 정보를 업데이트한다.
        None이 아닌 값만 반영하여 부분 수정(PATCH)을 지원한다.
        """
        for key, value in data.items():
            if value is not None:
                setattr(user, key, value)
        await self._session.commit()
        await self._session.refresh(user)

    async def hard_delete_user(self, user: User) -> None:
        """
        사용자 계정을 DB에서 영구 삭제한다. (복구 불가)
        Soft Delete(is_deleted 플래그)와 달리 실제 레코드를 제거한다.
        """
        await self._session.execute(
            delete(self._model).where(self._model.id == user.id)
        )
        await self._session.commit()
