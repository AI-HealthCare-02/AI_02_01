from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from app.dtos.base import BaseSerializerModel


class UserUpdateRequest(BaseModel):
    nickname: Annotated[str | None, Field(None, min_length=1, max_length=20)]
    gender: Annotated[str | None, Field(None, pattern=r"^[MF]$", description="'M' or 'F'")]
    birth_year: Annotated[int | None, Field(None, ge=1900, le=2026)]


class UserInfoResponse(BaseSerializerModel):
    id: int
    nickname: str
    role: str
    gender: str | None
    age: int | None
    birth_year: int | None
    character_stage: int
    current_point: int
    created_at: datetime
