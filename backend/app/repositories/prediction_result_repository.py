from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.health import HealthRecord
from app.models.prediction_results import PredictionResult, TriggerTypeEnum


class PredictionResultRepository:
    """
    PredictionResult 테이블에 대한 DB CRUD를 담당하는 레포지토리 클래스.
    서비스 계층(services/)에서 호출되며, SQLAlchemy AsyncSession을 통해 DB와 통신한다.
    """

    def __init__(self, session: AsyncSession):
        # 외부에서 주입받은 DB 세션 (FastAPI의 Depends를 통해 전달됨)
        self._session = session
        self._model = PredictionResult

    async def create(self, data: dict) -> PredictionResult:
        """
        예측 결과를 신규 저장.
        commit 후 refresh하여 DB 자동 생성 값(id, created_at)을 반영한다.
        """
        result = self._model(**data)
        self._session.add(result)
        await self._session.commit()
        await self._session.refresh(result)
        return result

    async def get_by_id(self, result_id: int) -> PredictionResult | None:
        """예측 결과 ID(PK)로 단건 조회. 없으면 None 반환."""
        row = await self._session.execute(select(self._model).where(self._model.id == result_id))
        return row.scalar_one_or_none()

    async def get_latest_by_record_id(self, record_id: int) -> PredictionResult | None:
        """특정 건강검진 기록의 가장 최근 예측 결과 단건 조회."""
        row = await self._session.execute(
            select(self._model)
            .where(self._model.record_id == record_id)
            .order_by(self._model.created_at.desc())
            .limit(1)
        )
        return row.scalar_one_or_none()

    async def get_list_by_record_id(self, record_id: int) -> list[PredictionResult]:
        """특정 건강검진 기록의 전체 예측 결과 목록 조회 (최신순)."""
        rows = await self._session.execute(
            select(self._model)
            .where(self._model.record_id == record_id)
            .order_by(self._model.created_at.desc())
        )
        return list(rows.scalars().all())

    async def get_list_by_user(self, user_id: int, limit: int = 20) -> list[PredictionResult]:
        """
        특정 사용자의 전체 예측 결과 목록 조회 (최신순, health_records JOIN).
        limit으로 최대 반환 건수를 제한한다.
        """
        rows = await self._session.execute(
            select(self._model)
            .join(HealthRecord, self._model.record_id == HealthRecord.id)
            .where(HealthRecord.user_id == user_id)
            .order_by(self._model.created_at.desc())
            .limit(limit)
        )
        return list(rows.scalars().all())

    async def get_latest_by_user(self, user_id: int) -> PredictionResult | None:
        """특정 사용자의 가장 최근 예측 결과 단건 조회."""
        row = await self._session.execute(
            select(self._model)
            .join(HealthRecord, self._model.record_id == HealthRecord.id)
            .where(HealthRecord.user_id == user_id)
            .order_by(self._model.created_at.desc())
            .limit(1)
        )
        return row.scalar_one_or_none()

    async def exists_by_record_and_trigger(self, record_id: int, trigger_type: TriggerTypeEnum) -> bool:
        """동일 건강검진 기록 + 트리거 타입 조합의 중복 저장 여부 확인."""
        row = await self._session.execute(
            select(self._model.id)
            .where(self._model.record_id == record_id)
            .where(self._model.trigger_type == trigger_type)
            .limit(1)
        )
        return row.scalar_one_or_none() is not None
