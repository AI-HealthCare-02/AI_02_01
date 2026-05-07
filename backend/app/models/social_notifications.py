from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SocialNotificationTypeEnum(StrEnum):
    CHEER = "cheer"


class SocialNotification(Base):
    __tablename__ = "social_notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="소셜 알림 ID")
    receiver_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, comment="알림 수신자")
    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, comment="알림 발신자")
    challenge_log_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("challenge_logs.id"),
        nullable=True,
        comment="응원 대상 챌린지 인증 로그",
    )
    type: Mapped[SocialNotificationTypeEnum] = mapped_column(
        Enum(SocialNotificationTypeEnum, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=SocialNotificationTypeEnum.CHEER,
        comment="알림 유형",
    )
    message: Mapped[str] = mapped_column(String(255), nullable=False, comment="알림 메시지")
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="읽은 시각")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), comment="알림 생성 시각"
    )
