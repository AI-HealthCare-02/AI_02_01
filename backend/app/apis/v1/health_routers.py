from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.databases import get_db_session
from app.dependencies.security import get_request_user
from app.dtos.health import (
    HealthRecordCreateRequest,
    HealthRecordListResponse,
    HealthRecordResponse,
    HealthRecordUpdateRequest,
)
from app.models.users import User
from app.services.health import HealthRecordService

# /api/v1/health 경로의 라우터. 건강검진 기록 CRUD API를 담당한다.
health_router = APIRouter(prefix="/health", tags=["health"])


@health_router.post(
    "/records",
    response_model=HealthRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="건강검진 기록 생성",
    description="건강검진 수치를 입력하여 새로운 기록을 생성한다. BMI는 서버에서 자동 계산된다.",
)
async def create_health_record(
    data: HealthRecordCreateRequest,  # 요청 body에서 건강검진 수치를 받음
    user: Annotated[User, Depends(get_request_user)],  # JWT 토큰으로 현재 로그인 사용자 확인
    session: Annotated[AsyncSession, Depends(get_db_session)],  # DB 세션 자동 주입
) -> Response:
    service = HealthRecordService(session)
    record = await service.create_record(data, user)
    return Response(record.model_dump(), status_code=status.HTTP_201_CREATED)


@health_router.get(
    "/records",
    response_model=HealthRecordListResponse,
    status_code=status.HTTP_200_OK,
    summary="건강검진 기록 목록 조회",
    description="로그인한 사용자의 건강검진 기록을 최신순으로 전체 조회한다.",
)
async def get_health_records(
    user: Annotated[User, Depends(get_request_user)],  # 로그인 사용자 확인
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    service = HealthRecordService(session)
    records = await service.get_records_by_user(user)
    return Response(records.model_dump(), status_code=status.HTTP_200_OK)


@health_router.get(
    "/records/{record_id}",
    response_model=HealthRecordResponse,
    status_code=status.HTTP_200_OK,
    summary="건강검진 기록 단건 조회",
    description="건강검진 기록 ID로 특정 기록을 조회한다.",
)
async def get_health_record(
    record_id: int,  # URL 경로에서 기록 ID를 받음
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    service = HealthRecordService(session)
    record = await service.get_record(record_id)
    return Response(record.model_dump(), status_code=status.HTTP_200_OK)


@health_router.patch(
    "/records/{record_id}",
    response_model=HealthRecordResponse,
    status_code=status.HTTP_200_OK,
    summary="건강검진 기록 수정",
    description="건강검진 기록을 부분 수정한다. 본인의 기록만 수정 가능하며, BMI는 키/몸무게 변경 시 자동 재계산된다.",
)
async def update_health_record(
    record_id: int,  # URL 경로에서 기록 ID를 받음
    data: HealthRecordUpdateRequest,  # 요청 body에서 수정할 데이터를 받음
    user: Annotated[User, Depends(get_request_user)],  # 본인 확인
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    service = HealthRecordService(session)
    record = await service.update_record(record_id, data, user)
    return Response(record.model_dump(), status_code=status.HTTP_200_OK)


@health_router.delete(
    "/records/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="건강검진 기록 삭제",
    description="건강검진 기록을 영구 삭제한다. 본인의 기록만 삭제 가능하다.",
)
async def delete_health_record(
    record_id: int,  # URL 경로에서 기록 ID를 받음
    user: Annotated[User, Depends(get_request_user)],  # 본인 확인
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    service = HealthRecordService(session)
    await service.delete_record(record_id, user)
