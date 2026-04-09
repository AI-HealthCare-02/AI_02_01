from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.health import HealthRecord


class HealthRecordRepository:
    """
    HealthRecord 테이블에 대한 DB CRUD를 담당하는 레포지토리 클래스.
    서비스 계층(services/)에서 호출되며, SQLAlchemy AsyncSession을 통해 DB와 통신한다.
    """

    def __init__(self, session: AsyncSession):
        # 외부에서 주입받은 DB 세션 (FastAPI의 Depends를 통해 전달됨)
        self._session = session
        self._model = HealthRecord

    async def create_record(self, data: dict[str, Any]) -> HealthRecord:
        """
        건강검진 수치를 신규 입력하고 DB에 저장.
        commit 후 refresh하여 DB에서 자동 생성된 값(id, created_at 등)을 반영한다.
        """
        record = self._model(**data)
        self._session.add(record)
        await self._session.commit()
        await self._session.refresh(record)
        return record

    async def get_record(self, record_id: int) -> HealthRecord | None:
        """
        건강검진 기록 ID(PK)로 단건 조회.
        없으면 None 반환.
        """
        result = await self._session.execute(select(self._model).where(self._model.id == record_id))
        return result.scalar_one_or_none()

    async def get_records_by_user(self, user_id: int) -> list[HealthRecord]:
        """
        특정 사용자의 건강검진 기록 전체 조회 (최신순 정렬).
        """
        result = await self._session.execute(
            select(self._model).where(self._model.user_id == user_id).order_by(self._model.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_record(self, record: HealthRecord, data: dict[str, Any]) -> None:
        """
        전달받은 dict 데이터로 건강검진 기록을 수정.
        None이 아닌 값만 반영하여 부분 수정(PATCH)을 지원한다.
        """
        for key, value in data.items():
            if value is not None:
                setattr(record, key, value)
        await self._session.commit()
        await self._session.refresh(record)

    async def delete_record(self, record_id: int) -> None:
        """
        건강검진 기록을 DB에서 영구 삭제. (복구 불가)
        """
        await self._session.execute(delete(self._model).where(self._model.id == record_id))
        await self._session.commit()
