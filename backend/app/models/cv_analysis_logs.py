from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# ── Enum 정의 ──
class AnalysisTypeEnum(StrEnum):
    DIET = "diet"
    HEALTH_CHECKUP = "health_checkup"
    EXERCISE = "exercise"


# CV 분석 결과 테이블 (GPT Vision API)
class CvAnalysisLog(Base):
    __tablename__ = "cv_analysis_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="CV 분석 결과 ID")
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, comment="FK → users")
    image_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="업로드 이미지 경로 (미사용 시 null)"
    )
    analysis_type: Mapped[AnalysisTypeEnum] = mapped_column(
        Enum(AnalysisTypeEnum, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        comment="diet / health_checkup / exercise",
    )
    result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="GPT Vision API 분석 결과")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), comment="분석 시각"
    )
