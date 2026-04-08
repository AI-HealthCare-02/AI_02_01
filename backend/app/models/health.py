from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# 건강검진 수치 입력 테이블
class HealthRecord(Base):
    __tablename__ = "health_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="건강검진 기록 ID")
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, comment="FK → users (비로그인 사용자는 null)"
    )
    systolic_bp: Mapped[int] = mapped_column(Integer, nullable=False, comment="수축기 혈압 (mmHg)")
    diastolic_bp: Mapped[int] = mapped_column(Integer, nullable=False, comment="이완기 혈압 (mmHg)")
    total_cholesterol: Mapped[int] = mapped_column(Integer, nullable=False, comment="총 콜레스테롤 (mg/dL)")
    glucose: Mapped[int] = mapped_column(Integer, nullable=False, comment="혈당 (mg/dL)")
    height: Mapped[Decimal] = mapped_column(Numeric(5, 1), nullable=False, comment="키 (cm)")
    weight: Mapped[Decimal] = mapped_column(Numeric(5, 1), nullable=False, comment="몸무게 (kg)")
    bmi: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), nullable=True, comment="BMI 자동 계산")
    smoke_yn: Mapped[bool] = mapped_column(Boolean, nullable=False, comment="흡연 여부")
    alcohol_yn: Mapped[bool] = mapped_column(Boolean, nullable=False, comment="음주 여부")
    exercise_yn: Mapped[bool] = mapped_column(Boolean, nullable=False, comment="규칙적 운동 여부")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), comment="입력 시각"
    )