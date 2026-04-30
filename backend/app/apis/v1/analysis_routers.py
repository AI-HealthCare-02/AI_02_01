import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import ORJSONResponse as Response
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.db.databases import get_db_session
from app.dependencies.security import get_optional_user, get_request_user
from app.dtos.analysis import (
    AnalysisResultResponse,
    AnalysisTaskResponse,
    GuestAnalysisRequest,
    MigrateGuestAnalysisRequest,
    PredictionResultListResponse,
    PredictionResultResponse,
    RecalculateRiskRequest,
)
from app.models.users import User
from app.services.analysis import HealthAnalysisService
from app.utils.pubsub import wait_task_result

logger = logging.getLogger("api.analysis")

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
    logger.info("[user_id=%d] 예측 이력 조회", user.id)
    service = HealthAnalysisService(session, redis)
    items = await service.get_prediction_history(user.id)
    logger.info("[user_id=%d] 예측 이력 조회 완료 - %d건", user.id, len(items))
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
    logger.info("[user_id=%d] record_id=%d 예측 결과 조회", user.id, record_id)
    service = HealthAnalysisService(session, redis)
    items = await service.get_prediction_result_by_record(record_id, user)
    logger.info("[user_id=%d] record_id=%d 예측 결과 조회 완료 - %d건", user.id, record_id, len(items))
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
    logger.info("[비회원] AI 분석 요청 - age=%s", data.age)
    service = HealthAnalysisService(session, redis)
    result = await service.request_guest_analysis(data)
    if isinstance(result, AnalysisTaskResponse):
        logger.info("[비회원] AI 분석 task 제출 - task_id=%s", result.task_id)
    else:
        logger.info("[비회원] AI 분석 캐시 히트 - 즉시 반환")
    return Response(result.model_dump(), status_code=status.HTTP_200_OK)


@analysis_router.post(
    "/migrate-guest",
    response_model=AnalysisResultResponse,
    status_code=status.HTTP_200_OK,
    summary="게스트 분석 결과 → 회원 계정 이전",
    description=(
        "비회원 분석 결과(guest_task_id)를 회원 건강검진 기록(record_id)에 연결하여 DB에 저장한다. "
        "재분석 없이 기존 결과를 그대로 이전하므로 즉시 반환된다. "
        "Celery 결과가 만료됐거나 없으면 404를 반환한다."
    ),
    responses={
        200: {"description": "이전 성공", "model": AnalysisResultResponse},
        403: {"description": "본인 기록이 아님"},
        404: {"description": "게스트 분석 결과 없음 또는 건강검진 기록 없음"},
    },
)
async def migrate_guest_analysis(
    data: MigrateGuestAnalysisRequest,
    user: Annotated[User, Depends(get_request_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> Response:
    logger.info(
        "[user_id=%d] 게스트 분석 이전 - guest_task_id=%s, record_id=%d", user.id, data.guest_task_id, data.record_id
    )
    service = HealthAnalysisService(session, redis)
    result = await service.migrate_guest_analysis(data.guest_task_id, data.record_id, user)
    logger.info("[user_id=%d] 게스트 분석 이전 완료 - record_id=%d", user.id, data.record_id)
    return Response(result.model_dump(), status_code=status.HTTP_200_OK)


@analysis_router.post(
    "/recalculate",
    response_model=AnalysisTaskResponse,
    status_code=status.HTTP_200_OK,
    summary="챌린지 달성 후 위험도 재예측",
    description=(
        "달성한 챌린지를 기반으로 건강 수치를 보정한 뒤 위험도를 재예측한다. "
        "completed_challenges에 달성한 챌린지 키를 전달한다. "
        "(smoke_7days / alco_7days / active_7days / diet_7days) "
        "결과 조회는 GET /{task_id}/wait 엔드포인트를 사용한다."
    ),
)
async def recalculate_risk_analysis(
    data: RecalculateRiskRequest,
    user: Annotated[User, Depends(get_request_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> Response:
    service = HealthAnalysisService(session, redis)
    result = await service.request_recalculate_analysis(data.record_id, data.completed_challenges, user)
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
    logger.info("[user_id=%d] AI 분석 요청 - record_id=%d", user.id, record_id)
    service = HealthAnalysisService(session, redis)
    result = await service.request_analysis(record_id, user)
    if isinstance(result, AnalysisTaskResponse):
        logger.info("[user_id=%d] AI 분석 task 제출 - record_id=%d, task_id=%s", user.id, record_id, result.task_id)
    else:
        logger.info("[user_id=%d] AI 분석 캐시 히트 - record_id=%d", user.id, record_id)
    return Response(result.model_dump(), status_code=status.HTTP_200_OK)


@analysis_router.get(
    "/{task_id}",
    response_model=AnalysisResultResponse,
    status_code=status.HTTP_200_OK,
    summary="AI 분석 현재 상태 즉시 확인",
    description=(
        "태스크의 현재 상태를 즉시 반환한다. "
        "결과가 없으면 pending을 반환하고 연결이 끊린다. "
        "실시간 결과 수신이 필요하면 GET /{task_id}/wait을 사용한다."
    ),
)
async def get_analysis_result(
    task_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> Response:
    if current_user is not None:
        raw_meta = await redis.get(f"ml1:task_meta:{task_id}")
        if raw_meta:
            meta = json.loads(raw_meta)
            task_user_id = meta.get("user_id")
            if task_user_id is not None and task_user_id != current_user.id:
                logger.warning(
                    "[user_id=%d] 불법 task 조회 시도 - task_id=%s (owner=%s)", current_user.id, task_id, task_user_id
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="본인의 분석 결과만 조회할 수 있습니다.",
                )
    service = HealthAnalysisService(session, redis)
    result = await service.get_analysis_result(task_id)
    logger.info("task 상태 조회 - task_id=%s, status=%s", task_id, result.status)
    return Response(result.model_dump(), status_code=status.HTTP_200_OK)


@analysis_router.get(
    "/{task_id}/wait",
    response_model=AnalysisResultResponse,
    status_code=status.HTTP_200_OK,
    summary="AI 분석 결과 조회 (롭 폴링)",
    description=(
        "결과가 준비될 때까지 서버에서 최대 30초 대기 후 반환한다.\n\n"
        "**롭 폴링 방식**\n"
        "- 결과 도착 즉시 응답 → 클라이언트 연결 유지 불필요\n"
        "- 30초 내 완료되면 즉시 반환, 타임아웃 시 `pending` 반환\n"
        "- 타임아웃 수신 시 클라이언트가 즉시 재요청\n\n"
        "**일반 폴링과 차이**\n"
        "- 일반 폴링: 서버가 즉시 pending 반환 → 클라이언트가 N초 후 재요청\n"
        "- 롭 폴링: 서버가 결과 올 때까지 대기 → 1회 요청으로 결과 수신"
    ),
)
async def wait_analysis_result(
    task_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> Response:
    if current_user is not None:
        raw_meta = await redis.get(f"ml1:task_meta:{task_id}")
        if raw_meta:
            meta = json.loads(raw_meta)
            task_user_id = meta.get("user_id")
            if task_user_id is not None and task_user_id != current_user.id:
                logger.warning(
                    "[user_id=%d] 불법 task wait 시도 - task_id=%s (owner=%s)", current_user.id, task_id, task_user_id
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="본인의 분석 결과만 조회할 수 있습니다.",
                )

    service = HealthAnalysisService(session, redis)

    result = await service.get_analysis_result(task_id)
    if result.status != "pending":
        logger.info("task 이미 완료 - task_id=%s, status=%s", task_id, result.status)
        return Response(result.model_dump(), status_code=status.HTTP_200_OK)

    logger.info("task 대기 시작 (Pub/Sub) - task_id=%s", task_id)
    data = await wait_task_result(task_id)

    if data is None:
        logger.warning("task 롭폴링 타임아웃 - task_id=%s", task_id)
        return Response(
            AnalysisResultResponse(status="pending").model_dump(),
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
        )

    final_result = await service.get_analysis_result(task_id)
    if final_result.status != "pending":
        logger.info("task 완료 - task_id=%s, status=%s", task_id, final_result.status)
        return Response(final_result.model_dump(), status_code=status.HTTP_200_OK)

    logger.info("task Pub/Sub 데이터 직접 반환 - task_id=%s", task_id)
    return Response(
        AnalysisResultResponse(
            status=data.get("status", "failed"),
            data=data.get("data"),
            error=data.get("error"),
        ).model_dump(),
        status_code=status.HTTP_200_OK,
    )
