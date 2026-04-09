import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# ── Enum 정의 ──
class PointReasonEnum(str, enum.Enum):
    CHALLENGE_COMPLETE = "challenge_complete"
    STREAK_BONUS = "streak_bonus"
    BADGE_EARNED = "badge_earned"
    DIET_REPORT = "diet_report"
    SHOP_PURCHASE = "shop_purchase"


# 포인트 변동 내역 테이블
class PointLog(Base):
    __tablename__ = "point_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="포인트 변동 ID")
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, comment="FK → users"
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False, comment="양수: 적립 / 음수: 차감")
    reason: Mapped[PointReasonEnum] = mapped_column(
        Enum(PointReasonEnum, values_callable=lambda x: [e.value for e in x]),
        nullable=False, comment="challenge_complete / streak_bonus / badge_earned / diet_report / shop_purchase"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), comment="변동 시각"
    )
