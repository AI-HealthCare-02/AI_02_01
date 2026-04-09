import logging

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.dtos.health import (
    HealthRecordCreateRequest,
    HealthRecordListResponse,
    HealthRecordResponse,
    HealthRecordUpdateRequest,
)
from app.models.health import HealthRecord
from app.models.users import User
from app.repositories.health_repository import HealthRecordRepository

logger = logging.getLogger(__name__)


class HealthRecordService:
    """건강검진 기록 CRUD 비즈니스 로직"""

    def __init__(self, session: AsyncSession):
        self.repo = HealthRecordRepository(session)

    @staticmethod
    def _calculate_bmi(height: float, weight: float) -> float:
        """BMI 계산 (체중(kg) / 신장(m)^2), 소수점 첫째 자리 반올림"""
        height_m = height / 100
        return round(weight / (height_m**2), 1)

    async def _get_record_with_permission(self, record_id: int, user: User) -> HealthRecord:
        """기록 존재 여부 및 소유권 검증 후 엔티티 반환"""
        record = await self.repo.get_record(record_id)
        if not record:
            logger.warning("존재하지 않는 기록 접근 시도 - record_id: %d", record_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 건강검진 기록을 찾을 수 없습니다.",
            )
        if record.user_id != user.id:
            logger.warning(
                "권한 없는 기록 접근 시도 - record_id: %d, owner: %s, requester: %d",
                record_id,
                record.user_id,
                user.id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="본인의 건강검진 기록만 수정/삭제할 수 있습니다.",
            )
        return record

    async def create_record(self, data: HealthRecordCreateRequest, user: User | None = None) -> HealthRecordResponse:
        """건강검진 기록 신규 생성 (BMI 자동 계산 포함)"""
        logger.info("건강검진 기록 생성 요청 - user_id: %s", user.id if user else "비로그인")

        record_dict = data.model_dump()
        record_dict["bmi"] = self._calculate_bmi(data.height, data.weight)

        if user:
            record_dict["user_id"] = user.id

        record = await self.repo.create_record(record_dict)
        logger.info("건강검진 기록 생성 완료 - record_id: %d", record.id)
        return HealthRecordResponse.model_validate(record)

    async def get_record(self, record_id: int) -> HealthRecordResponse:
        """건강검진 기록 단건 조회"""
        record = await self.repo.get_record(record_id)
        if not record:
            logger.warning("존재하지 않는 기록 조회 시도 - record_id: %d", record_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 건강검진 기록을 찾을 수 없습니다.",
            )
        return HealthRecordResponse.model_validate(record)

    async def get_records_by_user(self, user: User) -> HealthRecordListResponse:
        """로그인 사용자의 건강검진 기록 전체 조회"""
        records = await self.repo.get_records_by_user(user.id)
        logger.info("건강검진 기록 목록 조회 - user_id: %d, count: %d", user.id, len(records))
        return HealthRecordListResponse(records=[HealthRecordResponse.model_validate(r) for r in records])

    async def update_record(self, record_id: int, data: HealthRecordUpdateRequest, user: User) -> HealthRecordResponse:
        """건강검진 기록 수정 (PATCH, BMI 재계산 포함)"""
        record = await self._get_record_with_permission(record_id, user)

        update_dict = data.model_dump(exclude_none=True)

        # 키 또는 몸무게 변경 시 BMI 재계산
        if "height" in update_dict or "weight" in update_dict:
            new_height = update_dict.get("height", float(record.height))
            new_weight = update_dict.get("weight", float(record.weight))
            update_dict["bmi"] = self._calculate_bmi(new_height, new_weight)

        await self.repo.update_record(record, update_dict)
        logger.info("건강검진 기록 수정 완료 - record_id: %d", record_id)
        return HealthRecordResponse.model_validate(record)

    async def delete_record(self, record_id: int, user: User) -> None:
        """건강검진 기록 영구 삭제"""
        await self._get_record_with_permission(record_id, user)
        await self.repo.delete_record(record_id)
        logger.info("건강검진 기록 삭제 완료 - record_id: %d, user_id: %d", record_id, user.id)
