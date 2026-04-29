"""
건강검진 AI 분석 서비스

역할: 건강검진 데이터를 ML1 입력 형식으로 변환하고,
      Redis 캐시 확인 후 Celery task를 통해 AI Worker에 분석 요청
"""

import hashlib
import json
import logging

from celery import Celery
from celery.result import AsyncResult
from fastapi import HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.config import Config
from app.dtos.analysis import AnalysisResultResponse, AnalysisTaskResponse, GuestAnalysisRequest
from app.models.health import HealthRecord
from app.models.prediction_results import TriggerTypeEnum
from app.models.users import User
from app.repositories.health_repository import HealthRecordRepository
from app.repositories.prediction_result_repository import PredictionResultRepository

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Celery 클라이언트 역할별 분리
#
# send_task() 호출 시 Redis backend가 설정되어 있으면
# Pub/Sub result consumer를 즉시 구독 시도 → 연결 실패 시 RuntimeError 발생
#
# 해결: 발송과 결과 조회를 별도 앱으로 분리
#   - _celery_sender: broker만 설정 → Pub/Sub 구독 없음
#   - _celery_result: broker + backend 설정 → AsyncResult 조회 전용
# ──────────────────────────────────────────────
config = Config()

# 태스크 발송 전용 (Pub/Sub result consumer 미설정)
_celery_sender = Celery(broker=config.CELERY_BROKER_URL)

# 결과 조회 전용 (backend 필요)
_celery_result = Celery(
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_BACKEND_URL,  # DB 1: task 완료 결과 저장
)

# 캐시 TTL: 24시간
CACHE_TTL = 86400

# task_meta TTL: 24시간 (task_id → record_id 매핑 보존 기간)
TASK_META_TTL = 86400


class HealthAnalysisService:
    """건강검진 AI 분석 비즈니스 로직"""

    def __init__(self, session: AsyncSession, redis: Redis):
        self.health_repo = HealthRecordRepository(session)
        self.prediction_repo = PredictionResultRepository(session)
        self.redis = redis

    @property
    def repo(self) -> HealthRecordRepository:
        """하위 호환성 유지용 프로퍼티 (기존 self.repo 참조 유지)"""
        return self.health_repo

    async def request_analysis(self, record_id: int, user: User) -> AnalysisResultResponse | AnalysisTaskResponse:
        """
        AI 건강 분석 요청 처리.
        1. record_id로 DB에서 건강검진 기록 조회 + 소유권 검증
        2. 데이터를 ml1_run 입력 형식으로 변환
        3. Redis 캐시 확인 (hit → 즉시 반환)
        4. 캐시 miss → Celery task 제출 → task_id 반환
        """
        # 1. 건강검진 기록 조회 + 소유권 검증
        record = await self.repo.get_record(record_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 건강검진 기록을 찾을 수 없습니다.",
            )
        if record.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="본인의 건강검진 기록만 분석할 수 있습니다.",
            )

        # 2. ml1_run 입력 형식으로 변환
        user_data = self._convert_record_to_ml1_input(record, user)
        nickname = user.nickname
        challenge_days = 0  # 기본값 (추후 챌린지 진행일 연동 가능)

        # 3. Redis 캐시 확인 (DB 2)
        cache_key = self._build_cache_key(user_data, nickname, challenge_days)
        cached = await self.redis.get(cache_key)
        if cached:
            logger.info("ML1 캐시 히트 - user_id: %d, key: %s", user.id, cache_key)
            return AnalysisResultResponse(
                status="success",
                data=json.loads(cached),
            )

        # 4. Celery task 제출 (이름 기반 호출, AI 모듈 import 불필요)
        task = _celery_sender.send_task(
            "ml1.analyze_health",
            args=[user_data, nickname, challenge_days],
        )
        logger.info("ML1 분석 task 제출 - user_id: %d, task_id: %s", user.id, task.id)

        # 5. task_id → record_id 매핑을 Redis에 저장 (결과 수신 시 DB 저장에 사용)
        task_meta = json.dumps(
            {"record_id": record_id, "trigger_type": TriggerTypeEnum.NEW_RECORD.value, "user_id": user.id}
        )
        await self.redis.set(f"ml1:task_meta:{task.id}", task_meta, ex=TASK_META_TTL)

        return AnalysisTaskResponse(task_id=task.id, status="pending")

    async def request_guest_analysis(self, data: GuestAnalysisRequest) -> AnalysisResultResponse | AnalysisTaskResponse:
        """
        비회원 AI 건강 분석 요청 처리.
        DB 건강검진 기록 없이 요청 body의 수치를 직접 ML1 입력 형식으로 변환한다.
        1. 요청 수치를 ml1_run 입력 형식으로 변환
        2. Redis 캐시 확인 (hit → 즉시 반환)
        3. 캐시 miss → Celery task 제출 → task_id 반환
        """
        # 1. 요청 수치 → ml1_run 입력 형식 변환
        user_data = {
            "age": data.age,
            "gender": self._convert_gender(data.gender),
            "height": data.height,
            "weight": data.weight,
            "ap_hi": data.systolic_bp,
            "ap_lo": data.diastolic_bp,
            "cholesterol": self._convert_cholesterol(data.total_cholesterol),
            "gluc": self._convert_glucose(data.glucose),
            "smoke": int(data.smoke_yn),
            "alco": int(data.alcohol_yn),
            "active": int(data.exercise_yn),
        }
        nickname = "게스트"
        challenge_days = 0

        # 2. Redis 캐시 확인 (DB 2)
        cache_key = self._build_cache_key(user_data, nickname, challenge_days)
        cached = await self.redis.get(cache_key)
        if cached:
            logger.info("ML1 캐시 히트 (비회원) - key: %s", cache_key)
            return AnalysisResultResponse(status="success", data=json.loads(cached))

        # 3. Celery task 제출 (이름 기반 호출, AI 모듈 import 불필요)
        task = _celery_sender.send_task(
            "ml1.analyze_health",
            args=[user_data, nickname, challenge_days],
        )
        logger.info("ML1 분석 task 제출 (비회원) - task_id: %s", task.id)

        return AnalysisTaskResponse(task_id=task.id, status="pending")

    async def request_recalculate_analysis(
        self, record_id: int, completed_challenges: list[str], user: User
    ) -> AnalysisTaskResponse:
        """
        챌린지 달성 후 위험도 재예측 요청.
        1. record_id로 건강검진 기록 조회 + 소유권 검증
        2. 건강 수치를 ml1 입력 형식으로 변환
        3. Celery task 제출 → task_id 반환
        결과 조회는 기존 GET /{task_id}/wait 엔드포인트를 사용한다.
        """
        record = await self.health_repo.get_record(record_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 건강검진 기록을 찾을 수 없습니다.",
            )
        if record.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="본인의 건강검진 기록만 분석할 수 있습니다.",
            )

        user_data = self._convert_record_to_ml1_input(record, user)

        task = _celery_sender.send_task(
            "ml1.recalculate_risk",
            args=[user_data, completed_challenges, user.nickname or "사용자"],
        )
        logger.info("ML1 재계산 task 제출 - user_id: %d, task_id: %s", user.id, task.id)

        return AnalysisTaskResponse(task_id=task.id, status="pending")

    async def migrate_guest_analysis(self, guest_task_id: str, record_id: int, user: User) -> AnalysisResultResponse:
        """
        게스트 분석 결과를 회원 계정으로 이전.
        1. record_id 소유권 검증
        2. guest_task_id로 Celery 결과 조회
        3. prediction_results DB에 저장 후 반환
        """

        result = AsyncResult(id=guest_task_id, app=_celery_result)
        if result.state != "SUCCESS":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="게스트 분석 결과를 찾을 수 없습니다. 다시 분석해주세요."
            )

        task_result = result.result
        data = task_result.get("data") if isinstance(task_result, dict) else None
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게스트 분석 결과 데이터가 없습니다.")

        task_meta = json.dumps(
            {
                "record_id": record_id,
                "trigger_type": TriggerTypeEnum.NEW_RECORD.value,
                "user_id": user.id,
            }
        )
        await self.redis.set(f"ml1:task_meta:{guest_task_id}", task_meta, ex=TASK_META_TTL)
        await self._persist_prediction_result(guest_task_id, data)
        logger.info("게스트 분석 결과 회원 이전 완료 - user_id: %d, record_id: %d", user.id, record_id)

        return AnalysisResultResponse(status="success", data=data)

    async def get_analysis_result(self, task_id: str) -> AnalysisResultResponse:
        """
        Celery task 결과 조회 (DB 1에서 조회).
        - PENDING: 아직 처리 중
        - SUCCESS: 완료, 결과 반환
        - FAILURE: 실패, 에러 메시지 반환
        """
        result = AsyncResult(task_id, app=_celery_result)

        if result.state == "PENDING":
            return AnalysisResultResponse(status="pending")

        if result.state == "SUCCESS":
            task_result = result.result
            if isinstance(task_result, dict) and task_result.get("status") == "success":
                data = task_result.get("data")
                await self._persist_prediction_result(task_id, data)
                return AnalysisResultResponse(status="success", data=data)
            return AnalysisResultResponse(status="success", data=task_result)

        if result.state == "FAILURE":
            logger.error("ML1 분석 실패 - task_id: %s, error: %s", task_id, result.info)
            return AnalysisResultResponse(status="failed", error=str(result.info))

        # RETRY, STARTED 등 기타 상태
        return AnalysisResultResponse(status="pending")

    async def get_prediction_history(self, user_id: int, limit: int = 20) -> list:
        """
        사용자의 예측 결과 목록 조회 (최신순).
        prediction_results → health_records JOIN으로 본인 기록만 반환한다.
        """
        return await self.prediction_repo.get_list_by_user(user_id, limit=limit)

    async def get_prediction_result_by_record(self, record_id: int, user: User) -> list:
        """
        특정 건강검진 기록의 예측 결과 목록 조회.
        소유권 검증 후 반환한다.
        """
        record = await self.health_repo.get_record(record_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 건강검진 기록을 찾을 수 없습니다.",
            )
        if record.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="본인의 건강검진 기록만 조회할 수 있습니다.",
            )
        return await self.prediction_repo.get_list_by_record_id(record_id)

    async def _persist_prediction_result(self, task_id: str, data: dict | None) -> None:
        """
        Celery task 완료 시 예측 결과를 prediction_results DB에 저장.
        - Redis task_meta에서 record_id, trigger_type을 조회한다.
        - 중복 저장 방지: ml1:result_saved:{task_id} 플래그 확인
        - data가 없거나 task_meta가 없으면 조용히 종료 (비회원 분석 등)
        """
        if not data:
            return

        # 중복 저장 방지 확인
        saved_flag = await self.redis.get(f"ml1:result_saved:{task_id}")
        if saved_flag:
            return

        # task_meta에서 record_id, trigger_type 조회
        raw_meta = await self.redis.get(f"ml1:task_meta:{task_id}")
        if not raw_meta:
            # 비회원 분석 또는 메타 만료 → 저장 불필요
            return

        meta = json.loads(raw_meta)
        record_id = meta.get("record_id")
        trigger_type_value = meta.get("trigger_type", TriggerTypeEnum.NEW_RECORD.value)

        if not record_id:
            return

        # ML1 결과 데이터 파싱 (ml1_predict, ml1_comment 구조)
        # data.get()의 기본값 {}은 키가 없을 때만 적용되므로,
        # 키는 있지만 값이 None인 경우를 대비해 'or {}'로 None 방어 처리
        ml1_predict = data.get("ml1_predict") or {}
        ml1_comment = data.get("ml1_comment") or {}

        # predict()가 반환하는 한글 risk_grade → DB 영문 enum 변환
        _risk_grade_map = {
            "낮음": "low",
            "보통": "moderate",
            "중간": "medium",
            "높음": "high",
            "매우높음": "very_high",
        }
        risk_level = _risk_grade_map.get(ml1_predict.get("risk_grade", ""))

        prediction_data = {
            "record_id": record_id,
            "trigger_type": trigger_type_value,
            # predict() 반환 키: risk_percent, heart_age, risk_grade, top_risk_factors
            "cvd_risk_percent": ml1_predict.get("risk_percent"),
            "cvd_age": ml1_predict.get("heart_age"),
            "risk_level": risk_level,
            "top_risk_factors": ml1_predict.get("top_risk_factors"),
            # ml1_comment() (GPT 응답) 반환 키: evaluation, alert, missions, encouragement
            "ai_evaluation": ml1_comment.get("evaluation"),
            "ai_alert": ml1_comment.get("alert"),
            "ai_missions": ml1_comment.get("missions"),
            "ai_encouragement": ml1_comment.get("encouragement"),
        }

        # 필수 필드(cvd_risk_percent, cvd_age, risk_level) 누락 시 저장 스킵
        if not all([prediction_data["cvd_risk_percent"], prediction_data["cvd_age"], prediction_data["risk_level"]]):
            logger.warning("ML1 결과 필수 필드 누락 - task_id: %s, data: %s", task_id, ml1_predict)
            return

        try:
            await self.prediction_repo.create(prediction_data)
            # 중복 저장 방지 플래그 설정 (24시간 TTL)
            await self.redis.set(f"ml1:result_saved:{task_id}", "1", ex=TASK_META_TTL)
            logger.info("예측 결과 DB 저장 완료 - task_id: %s, record_id: %d", task_id, record_id)
        except Exception as e:
            # DB 저장 실패는 결과 반환에 영향을 주지 않도록 로그만 남김
            logger.error("예측 결과 DB 저장 실패 - task_id: %s, error: %s", task_id, e)

    # ──────────────────────────────────────────────
    # 데이터 변환 (private)
    # ──────────────────────────────────────────────

    @staticmethod
    def _validate_user_profile(user: User) -> None:
        """ml1_run 필수 필드(age, gender) 존재 여부 검증"""
        if user.age is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="AI 분석을 위해 사용자 나이 정보가 필요합니다. 프로필에서 나이를 먼저 입력해주세요.",
            )
        if user.gender is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="AI 분석을 위해 사용자 성별 정보가 필요합니다. 프로필에서 성별을 먼저 입력해주세요.",
            )

    @staticmethod
    def _convert_gender(gender: str) -> int:
        """성별 문자열 → 정수 변환 (M→2 남성, F→1 여성)"""
        gender_map = {"M": 2, "F": 1}
        result = gender_map.get(gender)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"유효하지 않은 성별 값입니다: {gender}",
            )
        return result

    @staticmethod
    def _convert_cholesterol(total_cholesterol: int) -> int:
        """총 콜레스테롤 (mg/dL) → 범주형 (1/2/3) 변환"""
        if total_cholesterol < 200:
            return 1  # 정상
        elif total_cholesterol < 240:
            return 2  # 경계
        else:
            return 3  # 높음

    @staticmethod
    def _convert_glucose(glucose: int) -> int:
        """공복 혈당 (mg/dL) → 범주형 (1/2/3) 변환"""
        if glucose < 100:
            return 1  # 정상
        elif glucose < 126:
            return 2  # 경계 (전당뇨)
        else:
            return 3  # 높음 (당뇨)

    def _convert_record_to_ml1_input(self, record: HealthRecord, user: User) -> dict:
        """HealthRecord 모델 → ml1_run 입력 dict 변환"""
        self._validate_user_profile(user)
        return {
            "age": user.age,
            "gender": self._convert_gender(user.gender),
            "height": float(record.height),
            "weight": float(record.weight),
            "ap_hi": record.systolic_bp,
            "ap_lo": record.diastolic_bp,
            "cholesterol": self._convert_cholesterol(record.total_cholesterol),
            "gluc": self._convert_glucose(record.glucose),
            "smoke": int(record.smoke_yn),
            "alco": int(record.alcohol_yn),
            "active": int(record.exercise_yn),
        }

    @staticmethod
    def _build_cache_key(user_data: dict, nickname: str, challenge_days: int) -> str:
        """입력 데이터 기반 Redis 캐시 키 생성 (MD5 해시)"""
        key_source = json.dumps(
            {"user_data": user_data, "nickname": nickname, "challenge_days": challenge_days},
            sort_keys=True,
        )
        return f"ml1:cache:{hashlib.md5(key_source.encode()).hexdigest()}"
