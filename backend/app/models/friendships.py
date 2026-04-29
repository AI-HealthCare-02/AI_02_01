from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# ── Enum 정의 ──
class FriendshipStatusEnum(StrEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"


# 친구 요청 테이블
class Friendship(Base):
    __tablename__ = "friendships"
    __table_args__ = (UniqueConstraint("requester_id", "receiver_id", name="uq_friendships_requester_receiver"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="친구 요청 ID")
    requester_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, comment="요청 보낸 사용자"
    )
    receiver_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, comment="요청 받은 사용자"
    )
    status: Mapped[FriendshipStatusEnum] = mapped_column(
        Enum(FriendshipStatusEnum, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        comment="PENDING / ACCEPTED / REJECTED / BLOCKED",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), comment="요청 시각"
    )
