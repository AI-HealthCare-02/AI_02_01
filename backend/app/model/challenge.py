from app.database import Base
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text


# 챌린지 마스터 테이블
class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="챌린지 ID",
    )
    category = Column(
        String,
        nullable=False,
        comment="smoking / drinking / diet / exercise / health",
    )
    title = Column(
        String,
        nullable=False,
        comment="챌린지 제목",
    )
    description = Column(
        Text,
        nullable=True,
        comment="챌린지 상세 설명",
    )
    verification_method = Column(
        String,
        nullable=False,
        comment="checklist / input / cv",
    )


# 사용자 챌린지 참여 테이블
class UserChallenge(Base):
    __tablename__ = "user_challenges"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="사용자 챌린지 참여 ID",
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        comment="FK → users",
    )
    challenge_id = Column(
        Integer,
        ForeignKey("challenges.id"),
        nullable=False,
        comment="FK → challenges",
    )
    status = Column(
        String,
        nullable=False,
        default="active",
        comment="active / completed / abandoned",
    )
    current_streak = Column(
        Integer,
        nullable=False,
        default=0,
        comment="연속 달성 일수 (7일 시 재예측)",
    )
    start_date = Column(
        Date,
        nullable=False,
        comment="시작 날짜",
    )
    completed_at = Column(
        DateTime,
        nullable=True,  # 완료 전까지는 null
        comment="완료 시각",
    )


# 챌린지 일별 인증 기록 테이블
class ChallengeLog(Base):
    __tablename__ = "challenge_logs"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="인증 기록 ID",
    )
    user_challenge_id = Column(
        Integer,
        ForeignKey("user_challenges.id"),
        nullable=False,
        comment="FK → user_challenges",
    )
    log_date = Column(
        Date,
        nullable=False,
        comment="인증 날짜",
    )
    verification_type = Column(
        String,
        nullable=False,
        comment="checklist / input / cv",
    )
    input_value = Column(
        String,
        nullable=True,  # checklist / cv 방식이면 null
        comment="수치 입력값 (개피수, 걸음수 등)",
    )
    cv_result_id = Column(
        Integer,
        ForeignKey("cv_analysis_logs.id"),
        nullable=True,  # cv 방식일 때만 사용
        comment="FK → cv_analysis_logs (cv 인증 시)",
    )
    created_at = Column(
        DateTime,
        nullable=False,
        comment="기록 생성 시각",
    )


# 뱃지 마스터 테이블
class Badge(Base):
    __tablename__ = "badges"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="뱃지 ID",
    )
    category = Column(
        String,
        nullable=False,
        comment="attendance / challenge / health / first / ranking / special",
    )
    name = Column(
        String,
        nullable=False,
        comment="뱃지 이름",
    )
    description = Column(
        Text,
        nullable=True,
        comment="획득 조건 설명",
    )
    reward_point = Column(
        Integer,
        nullable=False,
        default=0,
        comment="획득 시 지급 포인트",
        # 포인트 기준:
        # - 일반 뱃지  : +30pt
        # - 희귀 뱃지  : +100pt
        # - 전설 뱃지  : +300pt
        # - 건강 개선   : +500pt (심혈관 나이 -5세)
    )


# 사용자 뱃지 획득 기록 테이블
class UserBadge(Base):
    __tablename__ = "user_badges"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="사용자 뱃지 획득 ID",
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        comment="FK → users",
    )
    badge_id = Column(
        Integer,
        ForeignKey("badges.id"),
        nullable=False,
        comment="FK → badges",
    )
    acquired_at = Column(
        DateTime,
        nullable=False,
        comment="획득 시각",
    )


# 포인트 변동 이력 테이블
class PointLog(Base):
    __tablename__ = "point_logs"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="포인트 변동 ID",
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        comment="FK → users",
    )
    amount = Column(
        Integer,
        nullable=False,
        comment="양수: 적립 / 음수: 차감",
    )
    reason = Column(
        String,
        nullable=False,
        comment="challenge_complete / streak_bonus / badge_earned / diet_report / shop_purchase",
    )
    created_at = Column(
        DateTime,
        nullable=False,
        comment="변동 시각",
    )
