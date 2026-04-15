from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.databases import get_db_session
from app.dependencies.security import get_request_user
from app.dtos.users import (
    DashboardResponse,
    InitialProfileRequest,
    ProfileUpdateRequest,
    UserInfoResponse,
    WithdrawRequest,
    WithdrawResponse,
)
from app.models.users import User
from app.services.users import UserManageService

# /api/v1/users 경로의 라우터. 로그인된 사용자 관련 API를 담당한다.
user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.put(
    "/profile/initial",
    response_model=UserInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="초기 프로필 설정",
    description=(
        "Google 로그인 직후 성별과 출생 연도를 입력한다. "
        "나이는 서버에서 자동 계산되며, 성별은 최초 1회만 설정 가능하다."
    ),
    responses={
        409: {"description": "이미 초기 프로필이 설정된 사용자"},
    },
)
async def setup_initial_profile(
    data: InitialProfileRequest,  # 요청 body에서 gender, birth_year를 받음
    user: Annotated[User, Depends(get_request_user)],  # JWT 토큰으로 현재 로그인 사용자 확인
    session: Annotated[AsyncSession, Depends(get_db_session)],  # DB 세션 자동 주입
) -> Response:
    service = UserManageService(session)
    updated_user = await service.setup_initial_profile(user=user, data=data)
    return Response(
        UserInfoResponse.model_validate(updated_user).model_dump(),
        status_code=status.HTTP_200_OK,
    )


@user_router.patch(
    "/profile",
    response_model=UserInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="프로필 수정",
    description=(
        "로그인한 사용자의 닉네임, 프로필 이미지, 출생 연도를 수정한다. "
        "출생 연도 변경 시 나이가 자동 재계산된다. 성별은 수정할 수 없다."
    ),
)
async def update_profile(
    update_data: ProfileUpdateRequest,  # 요청 body에서 수정할 데이터를 받음
    user: Annotated[User, Depends(get_request_user)],  # JWT 토큰으로 현재 로그인 사용자 확인
    session: Annotated[AsyncSession, Depends(get_db_session)],  # DB 세션 자동 주입
) -> Response:
    service = UserManageService(session)
    updated_user = await service.update_profile(user=user, data=update_data)
    return Response(
        UserInfoResponse.model_validate(updated_user).model_dump(),
        status_code=status.HTTP_200_OK,
    )


@user_router.delete(
    "/withdraw",
    response_model=WithdrawResponse,
    status_code=status.HTTP_200_OK,
    summary="회원 탈퇴",
    description="로그인한 사용자의 계정을 탈퇴 처리한다. 탈퇴 사유는 선택 입력이며 최대 500자이다.",
)
async def withdraw_user(
    data: WithdrawRequest,
    user: Annotated[User, Depends(get_request_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    service = UserManageService(session)
    await service.withdraw_user(user, reason=data.reason)
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
    service = UserManageService(session)
    dashboard = await service.get_dashboard(user)
    return Response(
        dashboard.model_dump(),
        status_code=status.HTTP_200_OK,
    )
