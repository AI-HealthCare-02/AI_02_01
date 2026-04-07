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
from app.dtos.analysis import AnalysisResultResponse, AnalysisTaskResponse, HealthAnalysisRequest
from app.dtos.health import HealthRecordCreateRequest
from app.models.health import HealthRecord
from app.models.users import User
from app.repositories.health_repository import HealthRecordRepository

logger = logging.getLogger(__name__)

# Backend에서 Celery task를 이름 기반으로 호출 (AI 의존성 불필요)
config = Config()
_celery_broker_url = config.REDIS_URL.rsplit("/", 1)[0] + "/0"
celery_app = Celery(broker=_celery_broker_url, backend=_celery_broker_url)

# 캐시 TTL: 24시간
CACHE_TTL = 86400


class HealthAnalysisService:
    """건강검진 AI 분석 비즈니스 로직"""

    def __init__(self, session: AsyncSession, redis: Redis):
        self.repo = HealthRecordRepository(session)
        self.redis = redis

    async def request_analysis(
        self, request: HealthAnalysisRequest, user: User
    ) -> AnalysisResultResponse | AnalysisTaskResponse:
        """
        AI 건강 분석 요청 처리.
        1. record_id → DB 조회 / health_data → 직접 사용
        2. 데이터를 ml1_run 입력 형식으로 변환
        3. Redis 캐시 확인 (hit → 즉시 반환)
        4. 캐시 miss → Celery task 제출 → task_id 반환
        """
        # 1. 건강검진 데이터 획득
        if request.record_id is not None:
            record = await self.repo.get_record(request.record_id)
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
        else:
            user_data = self._convert_dto_to_ml1_input(request.health_data, user)

        nickname = user.nickname
        challenge_days = 0  # 기본값 (추후 챌린지 진행일 연동 가능)

        # 2. Redis 캐시 확인
        cache_key = self._build_cache_key(user_data, nickname, challenge_days)
        cached = await self.redis.get(cache_key)
        if cached:
            logger.info("ML1 캐시 히트 - user_id: %d, key: %s", user.id, cache_key)
            return AnalysisResultResponse(
                status="success",
                data=json.loads(cached),
            )

        # 3. Celery task 제출 (이름 기반 호출, AI 모듈 import 불필요)
        task = celery_app.send_task(
            "ml1.analyze_health",
            args=[user_data, nickname, challenge_days],
        )
        logger.info("ML1 분석 task 제출 - user_id: %d, task_id: %s", user.id, task.id)

        return AnalysisTaskResponse(task_id=task.id, status="pending")

    async def get_analysis_result(self, task_id: str) -> AnalysisResultResponse:
        """
        Celery task 결과 조회.
        - PENDING: 아직 처리 중
        - SUCCESS: 완료, 결과 반환
        - FAILURE: 실패, 에러 메시지 반환
        """
        result = AsyncResult(task_id, app=celery_app)

        if result.state == "PENDING":
            return AnalysisResultResponse(status="pending")

        if result.state == "SUCCESS":
            task_result = result.result
            # Celery task가 {"status": "success", "data": {...}} 형식으로 반환
            if isinstance(task_result, dict) and task_result.get("status") == "success":
                return AnalysisResultResponse(
                    status="success",
                    data=task_result.get("data"),
                )
            return AnalysisResultResponse(
                status="success",
                data=task_result,
            )

        if result.state == "FAILURE":
            logger.error("ML1 분석 실패 - task_id: %s, error: %s", task_id, result.info)
            return AnalysisResultResponse(
                status="failed",
                error=str(result.info),
            )

        # RETRY, STARTED 등 기타 상태
        return AnalysisResultResponse(status="pending")

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

    def _convert_dto_to_ml1_input(self, dto: HealthRecordCreateRequest, user: User) -> dict:
        """HealthRecordCreateRequest DTO → ml1_run 입력 dict 변환"""
        self._validate_user_profile(user)
        return {
            "age": user.age,
            "gender": self._convert_gender(user.gender),
            "height": dto.height,
            "weight": dto.weight,
            "ap_hi": dto.systolic_bp,
            "ap_lo": dto.diastolic_bp,
            "cholesterol": self._convert_cholesterol(dto.total_cholesterol),
            "gluc": self._convert_glucose(dto.glucose),
            "smoke": int(dto.smoke_yn),
            "alco": int(dto.alcohol_yn),
            "active": int(dto.exercise_yn),
        }

    @staticmethod
    def _build_cache_key(user_data: dict, nickname: str, challenge_days: int) -> str:
        """입력 데이터 기반 Redis 캐시 키 생성 (MD5 해시)"""
        key_source = json.dumps(
            {"user_data": user_data, "nickname": nickname, "challenge_days": challenge_days},
            sort_keys=True,
        )
        return f"ml1:cache:{hashlib.md5(key_source.encode()).hexdigest()}"
