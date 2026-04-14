from datetime import datetime
from typing import Any

from sqlalchemy import select
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

    async def soft_delete_user(self, user: User, reason: str | None = None) -> None:
        """
        사용자 계정을 Soft Delete 처리한다.
        is_deleted=True, deleted_at=현재 시각으로 설정하며 실제 레코드는 유지된다.
        탈퇴 사유(reason)가 전달되면 withdraw_reason에 저장한다.
        외래키 제약 조건(health_records 등 자식 테이블)을 위반하지 않는다.
        인증 의존성(get_request_user)에서 is_deleted=True인 사용자를 자동으로 차단한다.
        """
        user.is_deleted = True
        user.deleted_at = datetime.now()
        user.withdraw_reason = reason
        await self._session.commit()

    async def restore_user(self, user: User) -> None:
        """
        탈퇴 후 7일 이내 재로그인 시 계정을 복구한다.
        is_deleted=False, deleted_at=None, withdraw_reason=None으로 되돌리며
        기존 프로필 데이터는 모두 유지된다.
        """
        user.is_deleted = False
        user.deleted_at = None
        user.withdraw_reason = None
        await self._session.commit()
        await self._session.refresh(user)

    async def reset_user(self, user: User, nickname: str) -> None:
        """
        탈퇴 후 7일 초과 재로그인 시 계정을 초기 상태로 완전 리셋한다.
        프로필(gender, birth_year), 포인트, 캐릭터 단계, 탈퇴 사유를 초기화한다.
        nickname은 Google 계정 이름으로 갱신된다.
        """
        user.is_deleted = False
        user.deleted_at = None
        user.withdraw_reason = None
        user.nickname = nickname
        user.gender = None
        user.birth_year = None
        user.character_stage = 0
        user.current_point = 0
        await self._session.commit()
        await self._session.refresh(user)
