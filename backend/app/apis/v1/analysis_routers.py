from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.db.databases import get_db_session
from app.dependencies.security import get_request_user
from app.dtos.analysis import AnalysisResultResponse, AnalysisTaskResponse, GuestAnalysisRequest
from app.models.users import User
from app.services.analysis import HealthAnalysisService

# /api/v1/health/analysis 경로의 라우터. AI 건강 분석 API를 담당한다.
analysis_router = APIRouter(prefix="/health/analysis", tags=["analysis"])


@analysis_router.post(
    "/guest",
    response_model=AnalysisTaskResponse | AnalysisResultResponse,
    status_code=status.HTTP_200_OK,
    summary="비회원 AI 건강 분석 요청",
    description=(
        "로그인 없이 건강 수치를 직접 입력하여 심혈관 위험도 예측 및 건강 코멘트를 요청한다. "
        "캐시 히트 시 즉시 결과를 반환하고, 캐시 미스 시 task_id를 반환한다. "
        "결과 조회는 GET /{task_id} 엔드포인트를 사용한다."
    ),
)
async def request_guest_analysis(
    data: GuestAnalysisRequest,  # 요청 body에서 건강 수치를 직접 받음 (인증 불필요)
    session: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> Response:
    service = HealthAnalysisService(session, redis)
    result = await service.request_guest_analysis(data)
    return Response(result.model_dump(), status_code=status.HTTP_200_OK)


@analysis_router.post(
    "/{record_id}",
    response_model=AnalysisTaskResponse | AnalysisResultResponse,
    status_code=status.HTTP_200_OK,
    summary="AI 건강 분석 요청",
    description=(
        "건강검진 기록 ID를 기반으로 심혈관 위험도 예측 및 건강 코멘트를 요청한다. "
        "캐시 히트 시 즉시 결과를 반환하고, 캐시 미스 시 task_id를 반환한다."
    ),
)
async def request_analysis(
    record_id: int,  # URL 경로에서 건강검진 기록 ID를 받음
    user: Annotated[User, Depends(get_request_user)],  # JWT 토큰으로 현재 로그인 사용자 확인
    session: Annotated[AsyncSession, Depends(get_db_session)],  # DB 세션 자동 주입
    redis: Annotated[Redis, Depends(get_redis)],  # Redis 클라이언트 주입
) -> Response:
    service = HealthAnalysisService(session, redis)
    result = await service.request_analysis(record_id, user)
    return Response(result.model_dump(), status_code=status.HTTP_200_OK)


@analysis_router.get(
    "/{task_id}",
    response_model=AnalysisResultResponse,
    status_code=status.HTTP_200_OK,
    summary="AI 분석 결과 조회",
    description="비동기 AI 분석 작업의 결과를 조회한다. 작업이 완료되면 분석 결과를, 미완료 시 pending 상태를 반환한다.",
)
async def get_analysis_result(
    task_id: str,  # URL 경로에서 Celery task ID를 받음
    session: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> Response:
    service = HealthAnalysisService(session, redis)
    result = await service.get_analysis_result(task_id)
    return Response(result.model_dump(), status_code=status.HTTP_200_OK)
