from pydantic import BaseModel


class GoogleLoginRequest(BaseModel):
    code: str


class GoogleLoginResponse(BaseModel):
    access_token: str
    is_new_user: bool


class TokenRefreshResponse(BaseModel):
    access_token: str
