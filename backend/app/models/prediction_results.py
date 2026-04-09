import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# ── Enum 정의 ──
class TriggerTypeEnum(str, enum.Enum):
    NEW_RECORD = "new_record"
    CHALLENGE_STREAK = "challenge_streak"
    MANUAL = "manual"


class RiskLevelEnum(str, enum.Enum):
    LOW = "low"
    MODERATE = "moderate"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


# 심혈관 위험도 예측 결과 테이블
class PredictionResult(Base):
    __tablename__ = "prediction_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="예측 결과 ID")
    record_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("health_records.id"), nullable=False, comment="FK → health_records"
    )
    trigger_type: Mapped[TriggerTypeEnum] = mapped_column(
        Enum(TriggerTypeEnum, values_callable=lambda x: [e.value for e in x]),
        nullable=False, comment="new_record / challenge_streak / manual"
    )
    cvd_risk_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, comment="심혈관 발생 확률 (0~100%)")
    cvd_age: Mapped[int] = mapped_column(Integer, nullable=False, comment="심혈관 나이")
    risk_level: Mapped[RiskLevelEnum] = mapped_column(
        Enum(RiskLevelEnum, values_callable=lambda x: [e.value for e in x]),
        nullable=False, comment="low / moderate / medium / high / very_high"
    )
    top_risk_factors: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="SHAP 기반 위험 요인 상위 3개")
    ai_evaluation: Mapped[str | None] = mapped_column(Text, nullable=True, comment="ChatGPT 수치 평가 코멘트")
    ai_alert: Mapped[str | None] = mapped_column(Text, nullable=True, comment="ChatGPT 위험 경고 (없으면 null)")
    ai_missions: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="ChatGPT 추천 챌린지 3개")
    ai_encouragement: Mapped[str | None] = mapped_column(Text, nullable=True, comment="ChatGPT 동기부여 문장")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), comment="생성 시각"
    )
