from app.database import Base
from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text


# 건강검진 수치 입력 테이블
class HealthRecord(Base):
    __tablename__ = "health_records"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="건강검진 기록 ID",
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,                  # 비로그인 사용자도 입력 가능
        comment="FK → users",
    )
    systolic_bp = Column(
        Integer,
        nullable=False,
        comment="수축기 혈압 (mmHg)",
    )
    diastolic_bp = Column(
        Integer,
        nullable=False,
        comment="이완기 혈압 (mmHg)",
    )
    total_cholesterol = Column(
        Integer,
        nullable=False,
        comment="총 콜레스테롤 (mg/dL)",
    )
    glucose = Column(
        Integer,
        nullable=False,
        comment="혈당 (mg/dL)",
    )
    height = Column(
        Numeric(5, 1),                  # 예: 175.5
        nullable=False,
        comment="키 (cm)",
    )
    weight = Column(
        Numeric(5, 1),                  # 예: 72.3
        nullable=False,
        comment="몸무게 (kg)",
    )
    bmi = Column(
        Numeric(4, 1),                  # 예: 23.6 / 서버에서 자동 계산
        nullable=True,
        comment="BMI 자동 계산",
    )
    smoke_yn = Column(
        Boolean,
        nullable=False,
        comment="흡연 여부",
    )
    alcohol_yn = Column(
        Boolean,
        nullable=False,
        comment="음주 여부",
    )
    exercise_yn = Column(
        Boolean,
        nullable=False,
        comment="규칙적 운동 여부",
    )
    created_at = Column(
        DateTime,
        nullable=False,
        comment="입력 시각",
    )

# 심혈관 위험도 예측 결과 테이블
class PredictionResult(Base):
    __tablename__ = "prediction_results"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="예측 결과 ID",
    )
    record_id = Column(
        Integer,
        ForeignKey("health_records.id"),
        nullable=False,
        comment="FK → health_records",
    )
    trigger_type = Column(
        String,
        nullable=False,
        comment="new_record / challenge_streak / manual",
    )
    cvd_risk_percent = Column(
        Numeric(5, 2),                  # 예: 32.50 (0.00 ~ 100.00)
        nullable=False,
        comment="심혈관 발생 확률 (0~100%)",
    )
    cvd_age = Column(
        Integer,
        nullable=False,
        comment="심혈관 나이",
    )
    risk_level = Column(
        String,
        nullable=False,
        comment="low / moderate / medium / high / very_high",
    )
    top_risk_factors = Column(
        JSON,
        nullable=True,
        comment="SHAP 기반 위험 요인 상위 3개",
        # 저장 형태 예시:
        # [
        #   {"factor": "systolic_bp", "shap_value": 0.18, "value": 130},
        #   {"factor": "total_cholesterol", "shap_value": 0.14, "value": 220},
        #   {"factor": "smoke_yn", "shap_value": 0.11, "value": true}
        # ]
    )
    ai_evaluation = Column(
        Text,
        nullable=True,
        comment="ChatGPT 수치 평가 코멘트",
    )
    ai_alert = Column(
        Text,
        nullable=True,                  # 위험 수치 없으면 null
        comment="ChatGPT 위험 경고 (없으면 null)",
    )
    ai_missions = Column(
        JSON,
        nullable=True,
        comment="ChatGPT 추천 챌린지 3개",
        # 저장 형태 예시:
        # [
        #   {"title": "저염식사", "action": "나트륨 2000mg 이하", "reason": "혈압 감소 효과"},
        # ]
    )
    ai_encouragement = Column(
        Text,
        nullable=True,
        comment="ChatGPT 동기부여 문장",
    )
    created_at = Column(
        DateTime,
        nullable=False,
        comment="생성 시각",
    )
# CV(Computer Vision) 분석 결과 테이블.
class CvAnalysisLog(Base):
    __tablename__ = "cv_analysis_logs"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="CV 분석 결과 ID",
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        comment="FK → users",
    )
    image_url = Column(
        String,
        nullable=False,
        comment="업로드 이미지 경로 (S3 URL)",
    )
    analysis_type = Column(
        String,
        nullable=False,
        comment="diet / health_checkup / exercise",
    )
    result_json = Column(
        JSON,
        nullable=True,
        comment="GPT Vision API 분석 결과",
        # 저장 형태 예시 (diet):
        # {
        #   "detected_foods": ["된장찌개", "흰쌀밥"],
        #   "nutrients": {"carbohydrate": 58, "protein": 18, "fat": 15, "sodium": 9},
        #   "feedback": "단백질이 부족해요!"
        # }
    )
    created_at = Column(
        DateTime,
        nullable=False,
        comment="분석 시각",
    )
