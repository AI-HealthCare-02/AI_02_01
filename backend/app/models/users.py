from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Role(StrEnum):
    USER = "USER"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="사용자 고유 식별자")
    provider: Mapped[str] = mapped_column(String(20), nullable=False, default="google", comment="소셜 로그인 제공자 (현재 google만 지원)")
    provider_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, comment="소셜 로그인 제공자 고유 ID")
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="소셜 로그인 시 제공된 이메일")
    nickname: Mapped[str] = mapped_column(String(20), nullable=False, comment="서비스 전역 닉네임 (1~20자)")
    profile_image: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="프로필 이미지 URL")
    role: Mapped[str] = mapped_column(String(10), nullable=False, default=Role.USER, comment="USER / ADMIN")
    gender: Mapped[str | None] = mapped_column(String(1), nullable=True, comment="M: 남성 / F: 여성 (최초 입력 후 변경 불가)")
    age: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="현재 나이 (매년 birth_year 기준 자동 +1)")
    birth_year: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="출생 연도 (나이 자동 계산 기준)")
    character_stage: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="캐릭터 진화 단계 (0~3)")
    current_point: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="현재 보유 포인트")
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="탈퇴 여부 (Soft Delete)")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="탈퇴 처리 시각")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), comment="계정 생성 시각")
