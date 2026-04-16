"""
챌린지 라우터 — 챌린지 조회 / 선택 / 포기 / 챌린지 인증

위치: backend/app/apis/v1/challenge_routers.py
역할: HTTP 요청 수신 → ChallengeService로 비즈니스 로직 위임 → 응답 반환

패턴: auth_routers.py 패턴 준수
  - APIRouter with prefix & tags
  - JSONResponse 직접 반환
  - Swagger 문서화 (summary, description, responses)
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse as Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.databases import get_db_session
from app.dtos.challenge import (
    ChallengeListResponse,
    ChallengeLogRequest,
    ChallengeLogResponse,
    ChallengeResponse,
    ErrorResponse,
    MessageResponse,
    UserChallengeResponse,
)
from app.services.challenge_service import ChallengeService
from app.dependencies.security import get_request_user
from app.models.users import User

# /api/v1/challenges 경로의 라우터
challenge_router = APIRouter(prefix="/challenges", tags=["challenges"])

# /api/v1/user-challenges 경로의 라우터
user_challenge_router = APIRouter(prefix="/user-challenges", tags=["challenges"])


# ══════════════════════════════════════════════
# 1. 챌린지 목록 조회
# ══════════════════════════════════════════════

@challenge_router.get(
    "",
    response_model=ChallengeListResponse,
    status_code=status.HTTP_200_OK,
    summary="챌린지 목록 조회",
    description="전체 챌린지 풀 목록을 조회합니다. "
                "프론트에서 카테고리별 탭 필터링에 사용됩니다.",
    responses={
        200: {"description": "챌린지 목록 조회 성공", "model": ChallengeListResponse},
    },
)
async def get_challenges(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    service = ChallengeService(session)
    challenges = await service.get_all_challenges()

    return Response(
        content=ChallengeListResponse(
            challenges=[
                ChallengeResponse(
                    id=c.id,
                    category=c.category.value,
                    title=c.title,
                    description=c.description,
                    expected_effect=c.expected_effect,
                    verification_method=c.verification_method.value,
                    target_risk_factors=c.target_risk_factors,
                    duration_days=c.duration_days,
                    required_success_days=c.required_success_days,
                )
                for c in challenges
            ]
        ).model_dump(),
        status_code=status.HTTP_200_OK,
    )


# ══════════════════════════════════════════════
# 2. 챌린지 선택 (참여)
# ══════════════════════════════════════════════

@challenge_router.post(
    "/{challenge_id}/join",
    response_model=UserChallengeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="챌린지 참여 (시작하기)",
    description="챌린지를 선택하여 참여를 시작합니다. "
                "user_challenges 테이블에 active 상태로 등록됩니다.",
    responses={
        201: {"description": "챌린지 참여 성공", "model": UserChallengeResponse},
        404: {"description": "존재하지 않는 챌린지", "model": ErrorResponse},
        409: {"description": "이미 참여 중인 챌린지", "model": ErrorResponse},
    },
)
async def join_challenge(
    challenge_id: int,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_request_user)],
) -> Response:
    service = ChallengeService(session)
    user_challenge = await service.join_challenge(
        user_id=current_user.id,
        challenge_id=challenge_id,
    )

    return Response(
        content=UserChallengeResponse(
            id=user_challenge.id,
            user_id=user_challenge.user_id,
            challenge_id=user_challenge.challenge_id,
            status=user_challenge.status.value,
            current_streak=user_challenge.current_streak,
            start_date=user_challenge.start_date,
            completed_at=user_challenge.completed_at,
        ).model_dump(mode="json"),
        status_code=status.HTTP_201_CREATED,
    )


# ══════════════════════════════════════════════
# 3. 챌린지 포기
# ══════════════════════════════════════════════

@user_challenge_router.patch(
    "/{user_challenge_id}/abandon",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="챌린지 포기",
    description="진행 중인 챌린지를 포기합니다. "
                "status가 abandoned로 변경됩니다.",
    responses={
        200: {"description": "포기 처리 완료", "model": MessageResponse},
        400: {"description": "이미 완료/포기된 챌린지", "model": ErrorResponse},
        403: {"description": "본인 챌린지가 아님", "model": ErrorResponse},
        404: {"description": "존재하지 않는 참여 기록", "model": ErrorResponse},
    },
)
async def abandon_challenge(
    user_challenge_id: int,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_request_user)],
) -> Response:
    service = ChallengeService(session)
    await service.abandon_challenge(
        user_challenge_id=user_challenge_id,
        user_id=current_user.id,
    )

    return Response(
        content=MessageResponse(
            message="챌린지를 포기했습니다.",
        ).model_dump(),
        status_code=status.HTTP_200_OK,
    )


# ══════════════════════════════════════════════
# 4. 챌린지 인증
# ══════════════════════════════════════════════

@user_challenge_router.post(
    "/{user_challenge_id}/log",
    response_model=ChallengeLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="챌린지 인증",
    description="오늘의 챌린지 수행을 인증합니다. "
                "하루 1회만 가능하며, streak이 자동으로 업데이트됩니다. "
                "챌린지 성공/실패는 종료일 기준으로 최종 판정됩니다.",
    responses={
        201: {"description": "인증 성공", "model": ChallengeLogResponse},
        400: {"description": "이미 완료/포기된 챌린지", "model": ErrorResponse},
        403: {"description": "본인 챌린지가 아님", "model": ErrorResponse},
        404: {"description": "존재하지 않는 참여 기록", "model": ErrorResponse},
        409: {"description": "오늘 이미 인증 완료", "model": ErrorResponse},
    },
)
async def log_daily(
    user_challenge_id: int,
    request: ChallengeLogRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_request_user)],
) -> Response:
    service = ChallengeService(session)
    log = await service.log_daily(
        user_challenge_id=user_challenge_id,
        user_id=current_user.id,
        verification_type=request.verification_type,
        input_value=request.input_value,
        cv_result_id=request.cv_result_id,
    )

    return Response(
        content=ChallengeLogResponse(
            id=log.id,
            user_challenge_id=log.user_challenge_id,
            log_date=log.log_date,
            verification_type=log.verification_type.value,
            input_value=log.input_value,
            cv_result_id=log.cv_result_id,
            created_at=log.created_at,
        ).model_dump(mode="json"),
        status_code=status.HTTP_201_CREATED,
    )