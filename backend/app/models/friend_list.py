from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# 친구 목록 테이블
class FriendList(Base):
    __tablename__ = "friend_list"
    __table_args__ = (
        UniqueConstraint("user_id", "friend_id", name="uq_friend_list_user_friend"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="친구 목록 ID")
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, comment="사용자 ID"
    )
    friend_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, comment="친구 ID"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), comment="친구 확정 시각"
    )
