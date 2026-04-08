"""
ML2 Vision API 라우터 — 식단 분석 / 운동 캡처 인증 엔드포인트

위치: backend/app/apis/v1/ai_vision_routers.py
역할: 이미지 데이터 수신 → AIVisionService로 Celery 태스크 호출 → task_id 반환

패턴:auth_routers.py 패턴 준수
  - APIRouter with prefix & tags
  - JSONResponse 직접 반환
  - Swagger 문서화 (summary, description, responses)
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse as Response

from app.dtos.ai_vision import (
    ErrorResponse,
    ExerciseAnalyzeRequest,
    MealAnalyzeRequest,
    TaskResponse,
    TaskResultResponse,
)
from app.services.ai_vision_service import AIVisionService

# /api/v1/ai 경로의 라우터. tags=["ai-vision"]은 Swagger에서 그룹명으로 표시된다.
ai_vision_router = APIRouter(prefix="/ai", tags=["ai-vision"])

ai_vision_service = AIVisionService()


# ══════════════════════════════════════════════
# 식단 분석
# ══════════════════════════════════════════════

@ai_vision_router.post(
    "/meals/free",
    response_model=TaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="식단 무료 분석 요청 (+100pt)",
    description="식단 이미지를 제출하면 Celery 태스크로 분석을 시작합니다. "
                "task_id로 결과를 조회하세요.",
    responses={
        202: {"description": "분석 태스크 접수 완료", "model": TaskResponse},
        400: {"description": "잘못된 요청", "model": ErrorResponse},
    },
)
async def analyze_meal_free(request: MealAnalyzeRequest) -> Response:
    task_id = ai_vision_service.enqueue_meal_free(
        image_base64=request.image_base64,
        media_type=request.media_type,
        risk_factors=request.risk_factors,
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
    description="포인트를 사용하여 상세 영양 분석 리포트를 받습니다. "
                "비타민, 미네랄, 나트륨 정보 포함.",
    responses={
        202: {"description": "분석 태스크 접수 완료", "model": TaskResponse},
        400: {"description": "잘못된 요청", "model": ErrorResponse},
        402: {"description": "포인트 부족", "model": ErrorResponse},
    },
)
async def analyze_meal_paid(request: MealAnalyzeRequest) -> Response:
    # TODO: 포인트 차감 로직 추가 (user_id 필요 → 인증 미들웨어 연결 후)
    task_id = ai_vision_service.enqueue_meal_paid(
        image_base64=request.image_base64,
        media_type=request.media_type,
        risk_factors=request.risk_factors,
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
    description="운동 앱 스크린샷을 제출하여 운동 인증을 요청합니다.",
    responses={
        202: {"description": "인증 태스크 접수 완료", "model": TaskResponse},
        400: {"description": "잘못된 요청", "model": ErrorResponse},
    },
)
async def analyze_exercise(request: ExerciseAnalyzeRequest) -> Response:
    task_id = ai_vision_service.enqueue_exercise(
        image_base64=request.image_base64,
        media_type=request.media_type,
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
    summary="태스크 결과 조회",
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
