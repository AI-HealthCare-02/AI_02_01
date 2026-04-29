from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse as Response
from fastapi.responses import RedirectResponse
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

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"


@auth_router.get(
    "/google/login",
    summary="Google 로그인 시작",
    description="Google OAuth2 인증 페이지로 리다이렉트합니다.",
)
async def google_login() -> RedirectResponse:
    params = {
        "client_id": config.GOOGLE_CLIENT_ID,
        "redirect_uri": config.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
    }
    import logging

    logging.getLogger(__name__).info("Google login redirect_uri: %s", config.GOOGLE_REDIRECT_URI)
    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{urlencode(params)}")


@auth_router.post(
    "/login/google",
    response_model=SocialLoginResponse,
    summary="Google 로그인 처리",
)
async def google_login_post(
    request: SocialLoginRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    auth_service = AuthService(session)
    result = await auth_service.social_login(provider="google", code=request.code)

    response_status = status.HTTP_201_CREATED if result.is_new_user else status.HTTP_200_OK
    resp = Response(
        content=SocialLoginResponse(
            is_new_user=result.is_new_user,
            access_token=str(result.tokens["access_token"]),
            user=LoginUserResponse.model_validate(result.user),
        ).model_dump(),
        status_code=response_status,
    )
    resp.set_cookie(
        key="refresh_token",
        value=str(result.tokens["refresh_token"]),
        httponly=True,
        secure=True if config.ENV == Env.PROD else False,
        domain=config.COOKIE_DOMAIN or None,
        expires=result.tokens["access_token"].payload["exp"],
    )
    return resp


@auth_router.get(
    "/google/callback",
    summary="Google OAuth2 콜백",
    description="Google이 인가 코드와 함께 리다이렉트하는 엔드포인트입니다.",
)
async def google_callback(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RedirectResponse:
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="인가 코드가 없습니다.")

    auth_service = AuthService(session)
    result = await auth_service.social_login(provider="google", code=code)

    params = urlencode(
        {
            "access_token": str(result.tokens["access_token"]),
            "is_new_user": str(result.is_new_user).lower(),
            "user_id": result.user.id,
            "email": result.user.email or "",
            "name": result.user.nickname or "",
            "picture": result.user.profile_image or "",
        }
    )
    redirect = RedirectResponse(f"{config.FRONTEND_URL}/login/callback?{params}")
    redirect.set_cookie(
        key="refresh_token",
        value=str(result.tokens["refresh_token"]),
        httponly=True,
        secure=True if config.ENV == Env.PROD else False,
        domain=config.COOKIE_DOMAIN or None,
        expires=result.tokens["access_token"].payload["exp"],
    )
    return redirect


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
