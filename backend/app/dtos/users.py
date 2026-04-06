from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from app.dtos.base import BaseSerializerModel


class ProfileUpdateRequest(BaseModel):
    nickname: Annotated[str | None, Field(None, min_length=1, max_length=20, description="변경할 닉네임")]
    profile_image: Annotated[str | None, Field(None, max_length=512, description="프로필 이미지 URL")]


class UserInfoResponse(BaseSerializerModel):
    id: int
    email: str | None
    nickname: str
    profile_image: str | None
    role: str
    gender: str | None
    age: int | None
    birth_year: int | None
    character_stage: int
    current_point: int
    created_at: datetime


class DashboardResponse(BaseSerializerModel):
    nickname: str
    profile_image: str | None
    character_stage: int
    current_point: int
    gender: str | None
    age: int | None
    birth_year: int | None
    created_at: datetime


class WithdrawResponse(BaseModel):
    message: str
