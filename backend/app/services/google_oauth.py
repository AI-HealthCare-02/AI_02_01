import logging
import httpx
from fastapi import HTTPException, status
from pydantic import BaseModel

from app.core import config

# __name__: 현재 모듈 경로(app.services.auth)를 로거 이름으로 사용
# 로그 출력 시 어떤 파일에서 발생한 로그인지 자동 식별 가능
logger = logging.getLogger(__name__)


class GoogleUserInfo(BaseModel):
    sub: str
    name: str
    email: str | None = None
    picture: str | None = None


class GoogleOAuthService:
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

    async def exchange_code(self, code: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": config.GOOGLE_CLIENT_ID,
                    "client_secret": config.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": config.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )

            logger.info("code : %s", code)
            logger.info("client_id : %s", config.GOOGLE_CLIENT_ID)
            logger.info("client_secret : %s", config.GOOGLE_CLIENT_SECRET)
            logger.info("redirect_uri : %s", config.GOOGLE_REDIRECT_URI)
            logger.info("response : %s", response.json())

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google 인가 코드가 유효하지 않습니다.",
            )

        return response.json()

    async def get_user_info(self, access_token: str) -> GoogleUserInfo:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Google 사용자 정보를 가져올 수 없습니다.",
            )

        return GoogleUserInfo(**response.json())
