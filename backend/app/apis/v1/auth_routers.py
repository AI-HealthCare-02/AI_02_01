from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, status
from fastapi.responses import JSONResponse as Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import config
from app.core.config import Env
from app.db.databases import get_db_session
from app.dtos.auth import (
    ErrorResponse,
    LoginUserResponse,
    SocialLoginRequest,
    SocialLoginResponse,
    TokenRefreshResponse,
)
from app.services.auth import AuthService
from app.services.jwt import JwtService

# /api/v1/auth 경로의 라우터. tags=["auth"]는 Swagger에서 그룹명으로 표시된다.
auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post(
    "/login/{provider}",
    response_model=SocialLoginResponse,
    summary="소셜 로그인 및 회원가입 통합 API",
    description="소셜 로그인 제공자(google 등)의 인가 코드를 받아 로그인/회원가입을 처리합니다.",
    responses={
        200: {"description": "기존 회원 로그인 성공", "model": SocialLoginResponse},
        201: {"description": "신규 회원가입 성공", "model": SocialLoginResponse},
        400: {"description": "지원하지 않는 provider 또는 유효하지 않은 인가 코드", "model": ErrorResponse},
        422: {"description": "요청 데이터 형식 오류 (code 필드 누락 등)"},
        423: {"description": "비활성화된(탈퇴한) 계정", "model": ErrorResponse},
        502: {"description": "Google 서버 통신 오류", "model": ErrorResponse},
    },
)
async def social_login(
    provider: str,  # URL 경로에서 받는 소셜 제공자 (예: "google")
    request: SocialLoginRequest,  # 요청 body에서 인가 코드(code)를 받음
    session: Annotated[AsyncSession, Depends(get_db_session)],  # DB 세션 자동 주입
) -> Response:
    # AuthService에 DB 세션을 전달하여 로그인/회원가입 처리
    auth_service = AuthService(session)
    result = await auth_service.social_login(provider=provider, code=request.code)

    # 신규 가입 → 201 Created, 기존 로그인 → 200 OK
    response_status = status.HTTP_201_CREATED if result.is_new_user else status.HTTP_200_OK

    # 응답 body: access_token + is_new_user + 사용자 정보
    resp = Response(
        content=SocialLoginResponse(
            is_new_user=result.is_new_user,
            access_token=str(result.tokens["access_token"]),
            user=LoginUserResponse.model_validate(result.user),
        ).model_dump(),
        status_code=response_status,
    )

    # refresh_token은 httponly 쿠키에 저장 → JS에서 접근 불가하여 XSS 공격 방지
    resp.set_cookie(
        key="refresh_token",
        value=str(result.tokens["refresh_token"]),
        httponly=True,  # JavaScript에서 쿠키 접근 차단
        secure=True if config.ENV == Env.PROD else False,  # 운영 환경에서만 HTTPS 필수
        domain=config.COOKIE_DOMAIN or None,
        expires=result.tokens["access_token"].payload["exp"],
    )
    return resp


@auth_router.get(
    "/token/refresh",
    response_model=TokenRefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Access Token 갱신",
    description="Refresh Token(쿠키)을 사용하여 새로운 Access Token을 발급합니다.",
    responses={
        200: {"description": "토큰 갱신 성공", "model": TokenRefreshResponse},
        400: {"description": "유효하지 않은 Refresh Token", "model": ErrorResponse},
        401: {"description": "Refresh Token 없음 또는 만료", "model": ErrorResponse},
    },
)
async def token_refresh(
    jwt_service: Annotated[JwtService, Depends(JwtService)],  # JWT 처리 서비스 자동 주입
    refresh_token: Annotated[str | None, Cookie()] = None,  # 쿠키에서 refresh_token 자동 추출
) -> Response:
    # refresh_token 쿠키가 없으면 인증 실패
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is missing.",
        )
    # refresh_token을 검증하고 새로운 access_token 발급
    access_token = jwt_service.refresh_jwt(refresh_token)
    return Response(
        content=TokenRefreshResponse(access_token=str(access_token)).model_dump(),
        status_code=status.HTTP_200_OK,
    )
