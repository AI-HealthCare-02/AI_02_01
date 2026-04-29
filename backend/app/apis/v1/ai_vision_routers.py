"""
ML2 Vision API 라우터 — 식단 분석 / 운동 캡처 인증 엔드포인트

위치: backend/app/apis/v1/ai_vision_routers.py
역할: 이미지 파일 수신 → base64 변환 → AIVisionService로 Celery 태스크 호출 → task_id 반환

요청 방식: multipart/form-data
- 이미지: UploadFile (웹/모바일 파일 업로드 그대로 수신)
- 텍스트 필드: Form 파라미터
- MIME 타입: UploadFile.content_type에서 자동 감지
"""

import base64
import logging
from typing import Annotated

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse as Response
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.db.databases import get_db_session
from app.dependencies.security import get_request_user
from app.dtos.ai_vision import (
    ErrorResponse,
    TaskResponse,
    TaskResultResponse,
)
from app.models.users import User
from app.services.ai_vision_service import AIVisionService
from app.utils.pubsub import wait_task_result
from app.utils.s3 import upload_image

# 허용 MIME 타입 (OpenAI Vision API 지원 형식)
_ALLOWED_MEDIA_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

# /api/v1/ai 경로의 라우터. tags=["ai-vision"]은 Swagger에서 그룹명으로 표시된다.
ai_vision_router = APIRouter(prefix="/ai", tags=["ai-vision"])


def _validate_and_encode(image: UploadFile, image_bytes: bytes) -> tuple[str, str]:
    """
    이미지 파일 유효성 검사 후 base64 인코딩 반환.

    Returns:
        (image_base64, media_type) 튜플
    """
    media_type = image.content_type or "image/jpeg"

    if media_type not in _ALLOWED_MEDIA_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"지원하지 않는 이미지 형식입니다. 허용 형식: {', '.join(_ALLOWED_MEDIA_TYPES)}",
        )

    if len(image_bytes) > 20 * 1024 * 1024:  # 20MB 제한
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미지 크기는 20MB 이하여야 합니다.",
        )

    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    return image_base64, media_type


# ══════════════════════════════════════════════
# 식단 분석
# ══════════════════════════════════════════════


@ai_vision_router.post(
    "/meals/free",
    response_model=TaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="식단 무료 분석 요청 (+100pt)",
    description=(
        "식단 이미지를 multipart/form-data로 제출하면 Celery 태스크로 분석을 시작합니다. "
        "task_id로 결과를 조회하세요.\n\n"
        "**지원 형식:** JPEG, PNG, WebP, GIF (최대 20MB)"
    ),
    responses={
        202: {"description": "분석 태스크 접수 완료", "model": TaskResponse},
        400: {"description": "잘못된 요청 (지원하지 않는 형식 / 크기 초과)", "model": ErrorResponse},
    },
)
async def analyze_meal_free(
    image: Annotated[UploadFile, File(description="식단 이미지 파일 (JPEG, PNG, WebP, GIF)")],
    current_user: Annotated[User, Depends(get_request_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Redis, Depends(get_redis)],
    risk_factors: Annotated[str, Form(description="사용자 위험 요인 (예: 고혈압, 당뇨)")] = "",
    risk_grade: Annotated[str, Form(description="심혈관 위험 등급 (낮음/보통/중간/높음/매우높음)")] = "",
) -> Response:
    image_bytes = await image.read()
    image_base64, media_type = _validate_and_encode(image, image_bytes)
    try:
        image_url = await upload_image(image_bytes, media_type)
    except Exception as e:
        logger.warning("S3 업로드 실패 (meal_free) - 분석은 계속 진행: %s", e)
        image_url = None

    service = AIVisionService(session, redis)
    task_id = await service.enqueue_meal_free(
        image_base64=image_base64,
        media_type=media_type,
        user_id=current_user.id,
        image_url=image_url,
        risk_factors=risk_factors,
        risk_grade=risk_grade,
    )
    return Response(
        content=TaskResponse(
            task_id=task_id,
            status="PENDING",
            message="식단 무료 분석이 접수되었습니다.",
        ).model_dump(),
        status_code=status.HTTP_202_ACCEPTED,
    )


@ai_vision_router.post(
    "/meals/paid",
    response_model=TaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="식단 유료 상세 리포트 (-300pt)",
    description=(
        "포인트를 사용하여 상세 영양 분석 리포트를 받습니다. "
        "비타민, 미네랄, 나트륨 정보 포함.\n\n"
        "**지원 형식:** JPEG, PNG, WebP, GIF (최대 20MB)"
    ),
    responses={
        202: {"description": "분석 태스크 접수 완료", "model": TaskResponse},
        400: {"description": "잘못된 요청 (지원하지 않는 형식 / 크기 초과)", "model": ErrorResponse},
        402: {"description": "포인트 부족", "model": ErrorResponse},
    },
)
async def analyze_meal_paid(
    image: Annotated[UploadFile, File(description="식단 이미지 파일 (JPEG, PNG, WebP, GIF)")],
    current_user: Annotated[User, Depends(get_request_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Redis, Depends(get_redis)],
    risk_factors: Annotated[str, Form(description="사용자 위험 요인 (예: 고혈압, 당뇨)")] = "",
    risk_grade: Annotated[str, Form(description="심혈관 위험 등급 (낮음/보통/중간/높음/매우높음)")] = "",
) -> Response:
    # TODO: 포인트 차감 로직 추가 (current_user.id 사용)
    image_bytes = await image.read()
    image_base64, media_type = _validate_and_encode(image, image_bytes)
    try:
        image_url = await upload_image(image_bytes, media_type)
    except Exception as e:
        logger.warning("S3 업로드 실패 (meal_paid) - 분석은 계속 진행: %s", e)
        image_url = None

    service = AIVisionService(session, redis)
    task_id = await service.enqueue_meal_paid(
        image_base64=image_base64,
        media_type=media_type,
        user_id=current_user.id,
        image_url=image_url,
        risk_factors=risk_factors,
        risk_grade=risk_grade,
    )
    return Response(
        content=TaskResponse(
            task_id=task_id,
            status="PENDING",
            message="식단 유료 분석이 접수되었습니다. (-300pt)",
        ).model_dump(),
        status_code=status.HTTP_202_ACCEPTED,
    )


# ══════════════════════════════════════════════
# 운동 캡처 인증
# ══════════════════════════════════════════════


@ai_vision_router.post(
    "/exercise",
    response_model=TaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="운동 캡처 인증 (+100pt)",
    description=(
        "운동 앱 스크린샷을 multipart/form-data로 제출하여 운동 인증을 요청합니다.\n\n"
        "**지원 형식:** JPEG, PNG, WebP, GIF (최대 20MB)"
    ),
    responses={
        202: {"description": "인증 태스크 접수 완료", "model": TaskResponse},
        400: {"description": "잘못된 요청 (지원하지 않는 형식 / 크기 초과)", "model": ErrorResponse},
    },
)
async def analyze_exercise(
    image: Annotated[UploadFile, File(description="운동 앱 스크린샷 파일 (JPEG, PNG, WebP, GIF)")],
    current_user: Annotated[User, Depends(get_request_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> Response:
    image_bytes = await image.read()
    image_base64, media_type = _validate_and_encode(image, image_bytes)
    try:
        image_url = await upload_image(image_bytes, media_type)
    except Exception as e:
        logger.warning("S3 업로드 실패 (exercise) - 분석은 계속 진행: %s", e)
        image_url = None

    service = AIVisionService(session, redis)
    task_id = await service.enqueue_exercise(
        image_base64=image_base64,
        media_type=media_type,
        user_id=current_user.id,
        image_url=image_url,
    )
    return Response(
        content=TaskResponse(
            task_id=task_id,
            status="PENDING",
            message="운동 캡처 인증이 접수되었습니다.",
        ).model_dump(),
        status_code=status.HTTP_202_ACCEPTED,
    )


# ══════════════════════════════════════════════
# 태스크 결과 조회
# ══════════════════════════════════════════════


@ai_vision_router.get(
    "/tasks/{task_id}",
    response_model=TaskResultResponse,
    summary="태스크 현재 상태 즉시 확인",
    description=(
        "태스크의 현재 상태를 즉시 반환한다. "
        "결과가 없으면 PENDING을 반환하고 연결이 끊긴다. "
        "실시간 결과 수신이 필요하면 GET /tasks/{task_id}/wait을 사용한다."
    ),
    responses={
        200: {"description": "태스크 결과", "model": TaskResultResponse},
    },
)
async def get_task_result(
    task_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> Response:
    service = AIVisionService(session, redis)
    result = await service.get_task_result(task_id)
    return Response(
        content=TaskResultResponse(**result).model_dump(),
        status_code=status.HTTP_200_OK,
    )


@ai_vision_router.get(
    "/tasks/{task_id}/wait",
    response_model=TaskResultResponse,
    summary="태스크 결과 조회 (롱 폴링)",
    description=(
        "결과가 준비될 때까지 서버에서 최대 30초 대기 후 반환한다.\n\n"
        "**롱 폴링 방식**\n"
        "- 결과 도착 즉시 응답 → 클라이언트 연결 유지 불필요\n"
        "- 30초 내 완료되면 즉시 반환, 타임아웃 시 `PENDING` 반환\n"
        "- 타임아웃 수신 시 클라이언트가 즉시 재요청\n\n"
        "**일반 폴링과 차이**\n"
        "- 일반 폴링: 서버가 즉시 PENDING 반환 → 클라이언트가 N초 후 재요청\n"
        "- 롱 폴링: 서버가 결과 올 때까지 대기 → 1회 요청으로 결과 수신"
    ),
    responses={
        200: {"description": "태스크 결과 또는 PENDING(타임아웃)", "model": TaskResultResponse},
    },
)
async def wait_task_result_endpoint(
    task_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> Response:
    service = AIVisionService(session, redis)

    # 1. 이미 완료된 결과가 있으면 즉시 반환 (Pub/Sub 구독 불필요)
    result = await service.get_task_result(task_id)
    if result.get("status") not in ("PENDING", None):
        return Response(
            content=TaskResultResponse(**result).model_dump(),
            status_code=status.HTTP_200_OK,
        )

    # 2. 아직 처리 중 → Pub/Sub 채널 구독 후 최대 30초 대기
    data = await wait_task_result(task_id)

    if data is None:
        return Response(
            content=TaskResultResponse(task_id=task_id, status="PENDING", result=None, error=None).model_dump(),
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
        )

    # 3. 결과 도착 → get_task_result 재호출로 DB 저장 + 응답 반환
    result = await service.get_task_result(task_id)
    return Response(
        content=TaskResultResponse(**result).model_dump(),
        status_code=status.HTTP_200_OK,
    )
