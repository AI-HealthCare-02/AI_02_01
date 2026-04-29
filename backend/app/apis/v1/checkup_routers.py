"""
건강검진표 OCR 라우터 (REQ-HLTH-OCR)
CheckupService 직접 호출 → 수치 즉시 반환

식단/운동 분석과 달리 폼 자동완성 용도이므로 비동기 큐 없이 동기 응답.
"""

from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.dtos.ai_vision import ErrorResponse
from app.schemas.checkup import CheckupResponse
from app.services.checkup_service import CheckupService

_ALLOWED_MEDIA_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB

checkup_router = APIRouter(prefix="/ai", tags=["checkup"])

_service = CheckupService()


@checkup_router.post(
    "/checkup",
    response_model=CheckupResponse,
    status_code=status.HTTP_200_OK,
    summary="건강검진표 OCR 분석",
    description=(
        "건강검진 결과지 이미지를 업로드하면 수치를 즉시 추출하여 반환합니다.\n\n"
        "건강검진 결과지가 아닌 이미지는 `is_valid: false`로 반환됩니다.\n\n"
        "**지원 형식:** JPEG, PNG, WebP, GIF (최대 20MB)"
    ),
    responses={
        200: {"description": "OCR 분석 결과", "model": CheckupResponse},
        400: {"description": "잘못된 요청 (지원하지 않는 형식 / 크기 초과)", "model": ErrorResponse},
        500: {"description": "OCR 분석 실패 (API 오류 또는 파싱 오류)", "model": ErrorResponse},
    },
)
async def analyze_checkup(
    image: Annotated[UploadFile, File(description="건강검진 결과지 이미지 (JPEG, PNG, WebP, GIF)")],
) -> CheckupResponse:
    media_type = image.content_type or "image/jpeg"

    if media_type not in _ALLOWED_MEDIA_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"지원하지 않는 이미지 형식입니다. 허용 형식: {', '.join(_ALLOWED_MEDIA_TYPES)}",
        )

    image_bytes = await image.read()

    if len(image_bytes) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미지 크기는 20MB 이하여야 합니다.",
        )

    try:
        result = await _service.analyze(image_bytes, media_type)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e

    # TODO: cv_analysis_logs에 result_json 기록 (OCR 로그 저장)
    return CheckupResponse(**result)
