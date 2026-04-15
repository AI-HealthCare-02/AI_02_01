from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.db.databases import get_db_session
from app.dependencies.security import get_request_user
from app.dtos.analysis import (
    AnalysisResultResponse,
    AnalysisTaskResponse,
    GuestAnalysisRequest,
    PredictionResultListResponse,
    PredictionResultResponse,
)
from app.models.users import User
from app.services.analysis import HealthAnalysisService
from app.utils.pubsub import wait_task_result

# /api/v1/health/analysis 경로의 라우터. AI 건강 분석 API를 담당한다.
analysis_router = APIRouter(prefix="/health/analysis", tags=["analysis"])


@analysis_router.get(
    "/history",
    response_model=PredictionResultListResponse,
    status_code=status.HTTP_200_OK,
    summary="내 예측 결과 목록 조회",
    description="로그인한 사용자의 심혈관 위험도 예측 결과 목록을 최신순으로 반환한다. (최대 20건)",
)
async def get_prediction_history(
    user: Annotated[User, Depends(get_request_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> Response:
    service = HealthAnalysisService(session, redis)
    items = await service.get_prediction_history(user.id)
    result = PredictionResultListResponse(
        items=[PredictionResultResponse.model_validate(item) for item in items],
        total=len(items),
    )
    return Response(result.model_dump(), status_code=status.HTTP_200_OK)


@analysis_router.get(
    "/records/{record_id}/result",
    response_model=PredictionResultListResponse,
    status_code=status.HTTP_200_OK,
    summary="특정 건강검진의 예측 결과 목록 조회",
    description="건강검진 기록 ID로 해당 기록에 대한 심혈관 위험도 예측 결과 목록을 반환한다.",
)
async def get_prediction_results_by_record(
    record_id: int,
    user: Annotated[User, Depends(get_request_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> Response:
    service = HealthAnalysisService(session, redis)
    items = await service.get_prediction_result_by_record(record_id, user)
    result = PredictionResultListResponse(
        items=[PredictionResultResponse.model_validate(item) for item in items],
        total=len(items),
    )
    return Response(result.model_dump(), status_code=status.HTTP_200_OK)


@analysis_router.post(
    "/guest",
    response_model=AnalysisTaskResponse | AnalysisResultResponse,
    status_code=status.HTTP_200_OK,
    summary="비회원 AI 건강 분석 요청",
    description=(
        "로그인 없이 건강 수치를 직접 입력하여 심혈관 위험도 예측 및 건강 코멘트를 요청한다. "
        "캐시 히트 시 즉시 결과를 반환하고, 캐시 미스 시 task_id를 반환한다. "
        "결과 조회는 GET /{task_id}/wait 엔드포인트를 사용한다."
    ),
)
async def request_guest_analysis(
    data: GuestAnalysisRequest,
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
        "캐시 히트 시 즉시 결과를 반환하고, 캐시 미스 시 task_id를 반환한다. "
        "결과 조회는 GET /{task_id}/wait 엔드포인트를 사용한다."
    ),
)
async def request_analysis(
    record_id: int,
    user: Annotated[User, Depends(get_request_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> Response:
    service = HealthAnalysisService(session, redis)
    result = await service.request_analysis(record_id, user)
    return Response(result.model_dump(), status_code=status.HTTP_200_OK)


@analysis_router.get(
    "/{task_id}",
    response_model=AnalysisResultResponse,
    status_code=status.HTTP_200_OK,
    summary="AI 분석 현재 상태 즉시 확인",
    description=(
        "태스크의 현재 상태를 즉시 반환한다. "
        "결과가 없으면 pending을 반환하고 연결이 끊긴다. "
        "실시간 결과 수신이 필요하면 GET /{task_id}/wait을 사용한다."
    ),
)
async def get_analysis_result(
    task_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> Response:
    service = HealthAnalysisService(session, redis)
    result = await service.get_analysis_result(task_id)
    return Response(result.model_dump(), status_code=status.HTTP_200_OK)


@analysis_router.get(
    "/{task_id}/wait",
    response_model=AnalysisResultResponse,
    status_code=status.HTTP_200_OK,
    summary="AI 분석 결과 조회 (롱 폴링)",
    description=(
        "결과가 준비될 때까지 서버에서 최대 30초 대기 후 반환한다.\n\n"
        "**롱 폴링 방식**\n"
        "- 결과 도착 즉시 응답 → 클라이언트 연결 유지 불필요\n"
        "- 30초 내 완료되면 즉시 반환, 타임아웃 시 `pending` 반환\n"
        "- 타임아웃 수신 시 클라이언트가 즉시 재요청\n\n"
        "**일반 폴링과 차이**\n"
        "- 일반 폴링: 서버가 즉시 pending 반환 → 클라이언트가 N초 후 재요청\n"
        "- 롱 폴링: 서버가 결과 올 때까지 대기 → 1회 요청으로 결과 수신"
    ),
)
async def wait_analysis_result(
    task_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> Response:
    service = HealthAnalysisService(session, redis)

    # 1. 이미 완료된 결과가 있으면 즉시 반환 (Pub/Sub 구독 불필요)
    result = await service.get_analysis_result(task_id)
    if result.status != "pending":
        return Response(result.model_dump(), status_code=status.HTTP_200_OK)

    # 2. 아직 처리 중 → Pub/Sub 채널 구독 후 최대 30초 대기
    data = await wait_task_result(task_id)

    if data is None:
        # 타임아웃 → pending 반환, 클라이언트가 즉시 재요청
        return Response(
            AnalysisResultResponse(status="pending").model_dump(),
            status_code=status.HTTP_200_OK,
        )

    # 3. 결과 도착 → Celery backend에서 재조회하여 DB 저장 후 반환
    #    (Pub/Sub으로 받은 데이터와 동일하나, _persist_prediction_result 트리거 목적)
    final_result = await service.get_analysis_result(task_id)
    if final_result.status != "pending":
        return Response(final_result.model_dump(), status_code=status.HTTP_200_OK)

    # Celery backend 반영 지연 방어: Pub/Sub 데이터를 직접 반환
    return Response(
        AnalysisResultResponse(
            status=data.get("status", "failed"),
            data=data.get("data"),
            error=data.get("error"),
        ).model_dump(),
        status_code=status.HTTP_200_OK,
    )
