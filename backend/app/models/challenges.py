import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# ── Enum 정의 ──
class CategoryEnum(str, enum.Enum):
    DIET = "diet"
    EXERCISE = "exercise"
    LIFESTYLE = "lifestyle"


class VerificationMethodEnum(str, enum.Enum):
    CHECKLIST = "checklist"
    INPUT = "input"
    CV = "cv"


class UserChallengeStatusEnum(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    FAILED = "failed"


# 챌린지 마스터 테이블
class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="챌린지 ID")
    category: Mapped[CategoryEnum] = mapped_column(
        Enum(CategoryEnum, values_callable=lambda x: [e.value for e in x]),
        nullable=False, comment="diet / exercise / lifestyle"
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False, comment="챌린지 제목")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="챌린지 상세 설명")
    expected_effect: Mapped[str | None] = mapped_column(Text, nullable=True, comment="기대효과")
    verification_method: Mapped[VerificationMethodEnum] = mapped_column(
        Enum(VerificationMethodEnum, values_callable=lambda x: [e.value for e in x]),
        nullable=False, comment="checklist / input / cv"
    )
    target_risk_factors: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="쉼표 구분 대상 위험 요인 (예: 고혈압,과체중)")
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False, comment="전체 수행 기간 (일)")
    required_success_days: Mapped[int] = mapped_column(Integer, nullable=False, comment="완료 인정을 위한 최소 인증 일수")


# 사용자 챌린지 참여 테이블
class UserChallenge(Base):
    __tablename__ = "user_challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="사용자 챌린지 참여 ID")
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, comment="FK → users"
    )
    challenge_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("challenges.id"), nullable=False, comment="FK → challenges"
    )
    status: Mapped[UserChallengeStatusEnum] = mapped_column(
        Enum(UserChallengeStatusEnum, values_callable=lambda x: [e.value for e in x]),
        nullable=False, comment="active / completed / abandoned"
    )
    current_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="연속 달성 일수 (7일 시 재예측)")
    start_date: Mapped[date] = mapped_column(Date, nullable=False, comment="시작 날짜")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="완료 시각")


# 챌린지 인증 기록 테이블
class ChallengeLog(Base):
    __tablename__ = "challenge_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="인증 기록 ID")
    user_challenge_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user_challenges.id"), nullable=False, comment="FK → user_challenges"
    )
    log_date: Mapped[date] = mapped_column(Date, nullable=False, comment="인증 날짜")
    verification_type: Mapped[VerificationMethodEnum] = mapped_column(
        Enum(VerificationMethodEnum, values_callable=lambda x: [e.value for e in x]),
        nullable=False, comment="checklist / input / cv"
    )
    input_value: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="수치 입력값 (개피수, 걸음수 등)")
    cv_result_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("cv_analysis_logs.id"), nullable=True, comment="FK → cv_analysis_logs (cv 인증 시)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), comment="기록 생성 시각"
    )
