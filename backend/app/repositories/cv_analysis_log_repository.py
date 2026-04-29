from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cv_analysis_logs import CvAnalysisLog


class CvAnalysisLogRepository:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._model = CvAnalysisLog

    async def create(self, data: dict) -> CvAnalysisLog:
        log = self._model(**data)
        self._session.add(log)
        await self._session.commit()
        await self._session.refresh(log)
        return log

    async def get_list_by_user(self, user_id: int, limit: int = 20) -> list[CvAnalysisLog]:
        rows = await self._session.execute(
            select(self._model)
            .where(self._model.user_id == user_id)
            .order_by(self._model.created_at.desc())
            .limit(limit)
        )
        return list(rows.scalars().all())
