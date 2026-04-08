from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.dtos.base import BaseSerializerModel


class InitialProfileRequest(BaseModel):
    """초기 프로필 설정 요청 (Google 로그인 직후 1회)"""

    gender: Annotated[Literal["M", "F"], Field(description="성별 (M: 남성, F: 여성, 최초 1회만 설정 가능)")]
    birth_year: Annotated[int, Field(ge=1900, le=2026, description="출생 연도 (age 자동 계산 기준)")]
    nickname: Annotated[
        str | None, Field(None, min_length=1, max_length=20, description="변경할 닉네임 (미입력 시 유지)")
    ]


class ProfileUpdateRequest(BaseModel):
    """프로필 수정 요청 (gender는 수정 불가)"""

    nickname: Annotated[str | None, Field(None, min_length=1, max_length=20, description="변경할 닉네임")]
    profile_image: Annotated[str | None, Field(None, max_length=512, description="프로필 이미지 URL")]
    birth_year: Annotated[int | None, Field(None, ge=1900, le=2026, description="출생 연도 변경 (age 자동 재계산)")]


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
