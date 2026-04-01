from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Cookie, Depends, HTTPException, status
from fastapi.responses import JSONResponse as Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import config
from app.core.config import Env
from app.db.databases import get_db_session
from app.dtos.auth import GoogleLoginRequest, GoogleLoginResponse, TokenRefreshResponse
from app.services.auth import AuthService
from app.services.google_oauth import GoogleOAuthService
from app.services.jwt import JwtService

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.get("/google/authorize")
async def google_authorize() -> dict:
    params = urlencode(
        {
            "client_id": config.GOOGLE_CLIENT_ID,
            "redirect_uri": config.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
        }
    )
    return {"authorization_url": f"https://accounts.google.com/o/oauth2/v2/auth?{params}"}


@auth_router.post("/google/login", response_model=GoogleLoginResponse, status_code=status.HTTP_200_OK)
async def google_login(
    request: GoogleLoginRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    google_oauth: Annotated[GoogleOAuthService, Depends(GoogleOAuthService)],
) -> Response:
    token_data = await google_oauth.exchange_code(request.code)
    google_user = await google_oauth.get_user_info(token_data["access_token"])
    auth_service = AuthService(session)
    tokens, is_new_user = await auth_service.google_login(google_user)

    resp = Response(
        content=GoogleLoginResponse(
            access_token=str(tokens["access_token"]),
            is_new_user=is_new_user,
        ).model_dump(),
        status_code=status.HTTP_200_OK,
    )
    resp.set_cookie(
        key="refresh_token",
        value=str(tokens["refresh_token"]),
        httponly=True,
        secure=True if config.ENV == Env.PROD else False,
        domain=config.COOKIE_DOMAIN or None,
        expires=tokens["access_token"].payload["exp"],
    )
    return resp


@auth_router.get("/token/refresh", response_model=TokenRefreshResponse, status_code=status.HTTP_200_OK)
async def token_refresh(
    jwt_service: Annotated[JwtService, Depends(JwtService)],
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> Response:
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is missing.")
    access_token = jwt_service.refresh_jwt(refresh_token)
    return Response(
        content=TokenRefreshResponse(access_token=str(access_token)).model_dump(), status_code=status.HTTP_200_OK
    )
