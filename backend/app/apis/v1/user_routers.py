from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.databases import get_db_session
from app.dependencies.security import get_request_user
from app.dtos.users import (
    DashboardResponse,
    ProfileUpdateRequest,
    UserInfoResponse,
    WithdrawResponse,
)
from app.models.users import User
from app.services.users import UserManageService

# /api/v1/users 경로의 라우터. 로그인된 사용자 관련 API를 담당한다.
user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.patch(
    "/profile",
    response_model=UserInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="프로필 수정",
    description="로그인한 사용자의 닉네임 및 프로필 이미지를 수정한다. 수정 즉시 전체 화면에 반영된다.",
)
async def update_profile(
    update_data: ProfileUpdateRequest,  # 요청 body에서 수정할 데이터를 받음
    user: Annotated[User, Depends(get_request_user)],  # JWT 토큰으로 현재 로그인 사용자 확인
    session: Annotated[AsyncSession, Depends(get_db_session)],  # DB 세션 자동 주입
) -> Response:
    user_manage_service = UserManageService(session)
    updated_user = await user_manage_service.update_profile(user=user, data=update_data)
    # model_validate: SQLAlchemy 모델 → Pydantic 응답 DTO로 변환
    return Response(
        UserInfoResponse.model_validate(updated_user).model_dump(),
        status_code=status.HTTP_200_OK,
    )


@user_router.delete(
    "/withdraw",
    response_model=WithdrawResponse,
    status_code=status.HTTP_200_OK,
    summary="회원 탈퇴",
    description="로그인한 사용자의 계정과 모든 관련 데이터를 영구적으로 삭제한다.",
)
async def withdraw_user(
    user: Annotated[User, Depends(get_request_user)],  # 탈퇴할 사용자 본인 확인
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    user_manage_service = UserManageService(session)
    await user_manage_service.withdraw_user(user)
    return Response(
        WithdrawResponse(message="회원 탈퇴가 완료되었습니다.").model_dump(),
        status_code=status.HTTP_200_OK,
    )


@user_router.get(
    "/dashboard",
    response_model=DashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="마이페이지 대시보드 조회",
    description="로그인한 사용자의 건강 현황 요약 정보를 반환한다.",
)
async def get_dashboard(
    user: Annotated[User, Depends(get_request_user)],  # 로그인 사용자 확인
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    user_manage_service = UserManageService(session)
    dashboard = await user_manage_service.get_dashboard(user)
    return Response(
        dashboard.model_dump(),
        status_code=status.HTTP_200_OK,
    )
