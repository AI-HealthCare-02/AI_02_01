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
import json
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse as Response
from fastapi.responses import StreamingResponse

from app.dtos.ai_vision import (
    ErrorResponse,
    TaskResponse,
    TaskResultResponse,
)
from app.services.ai_vision_service import AIVisionService
from app.utils.pubsub import stream_task_result

# 허용 MIME 타입 (OpenAI Vision API 지원 형식)
_ALLOWED_MEDIA_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

# /api/v1/ai 경로의 라우터. tags=["ai-vision"]은 Swagger에서 그룹명으로 표시된다.
ai_vision_router = APIRouter(prefix="/ai", tags=["ai-vision"])

ai_vision_service = AIVisionService()


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
    risk_factors: Annotated[str, Form(description="사용자 위험 요인 (예: 고혈압, 당뇨)")] = "",
) -> Response:
    image_bytes = await image.read()
    image_base64, media_type = _validate_and_encode(image, image_bytes)

    task_id = ai_vision_service.enqueue_meal_free(
        image_base64=image_base64,
        media_type=media_type,
        risk_factors=risk_factors,
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
    risk_factors: Annotated[str, Form(description="사용자 위험 요인 (예: 고혈압, 당뇨)")] = "",
) -> Response:
    # TODO: 포인트 차감 로직 추가 (user_id 필요 → 인증 미들웨어 연결 후)
    image_bytes = await image.read()
    image_base64, media_type = _validate_and_encode(image, image_bytes)

    task_id = ai_vision_service.enqueue_meal_paid(
        image_base64=image_base64,
        media_type=media_type,
        risk_factors=risk_factors,
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
) -> Response:
    image_bytes = await image.read()
    image_base64, media_type = _validate_and_encode(image, image_bytes)

    task_id = ai_vision_service.enqueue_exercise(
        image_base64=image_base64,
        media_type=media_type,
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
    summary="태스크 결과 조회 (폴링)",
    description="task_id로 Celery 태스크의 상태와 결과를 조회합니다.",
    responses={
        200: {"description": "태스크 결과", "model": TaskResultResponse},
    },
)
async def get_task_result(task_id: str) -> Response:
    result = ai_vision_service.get_task_result(task_id)
    return Response(
        content=TaskResultResponse(**result).model_dump(),
        status_code=status.HTTP_200_OK,
    )


@ai_vision_router.get(
    "/tasks/{task_id}/stream",
    summary="태스크 결과 실시간 수신 (SSE)",
    description=(
        "Redis Pub/Sub을 통해 Vision AI 분석 완료 결과를 실시간으로 수신한다.\n\n"
        "**SSE(Server-Sent Events) 방식**: 연결 후 결과가 도착하면 즉시 수신하고 연결이 종료된다.\n\n"
        "**이벤트 종류**\n"
        "- `connected`: 구독 연결 확인 (최초 1회)\n"
        "- `data`: 분석 완료 결과 (JSON)\n"
        "- `timeout`: 120초 초과 시 연결 종료\n"
        "- `error`: 서버 오류\n\n"
        "**폴링 방식과 비교**: 반복 요청 없이 결과 즉시 수신 가능"
    ),
    response_class=StreamingResponse,
)
async def stream_vision_result(task_id: str) -> StreamingResponse:
    # 이미 완료된 태스크라면 SSE 없이 즉시 반환
    result = ai_vision_service.get_task_result(task_id)
    if result.get("status") not in ("PENDING", None):

        async def _immediate():
            yield f"event: connected\ndata: {json.dumps({'task_id': task_id})}\n\n"
            yield f"data: {json.dumps(result)}\n\n"

        return StreamingResponse(
            _immediate(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # 대기 중 → Pub/Sub 채널 구독 후 결과 도착 시 SSE 전달
    return StreamingResponse(
        stream_task_result(task_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
