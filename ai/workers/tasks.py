"""
ML1 Celery Task 정의
건강검진 수치 → XGBoost 위험도 예측 + ChatGPT 건강 코멘트 생성
"""

import hashlib
import json
import logging
import os

import redis

from ai.celery_app import celery_app
from ai.workers.worker import ml1_run

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Redis 캐시 클라이언트 (DB 2번 - ML1 분석 결과 캐시 전용)
# ──────────────────────────────────────────────
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
# DB 1번으로 변경하여 Celery broker(DB 0번)와 분리
CACHE_REDIS_URL = os.getenv("REDIS_CACHE_URL", REDIS_URL.rsplit("/", 1)[0] + "/2")
cache_redis = redis.from_url(CACHE_REDIS_URL, decode_responses=True)

# 캐시 TTL: 24시간
CACHE_TTL = 86400


def _build_cache_key(user_data: dict, nickname: str, challenge_days: int) -> str:
    """캐시 키 생성 (입력 데이터의 MD5 해시)"""
    key_source = json.dumps({"user_data": user_data, "nickname": nickname, "challenge_days": challenge_days}, sort_keys=True)
    return f"ml1:cache:{hashlib.md5(key_source.encode()).hexdigest()}"


# ──────────────────────────────────────────────
# ML1 분석 Celery Task
# ──────────────────────────────────────────────
@celery_app.task(
    name="ml1.analyze_health",
    bind=True,
    max_retries=2,
    default_retry_delay=5,
)
def analyze_health(self, user_data: dict, nickname: str = "사용자", challenge_days: int = 0) -> dict:
    """
    건강검진 수치 → XGBoost 예측 + GPT 코멘트 (Celery task)

    Args:
        user_data: ml1_run 입력 형식 (age, gender, height, weight, ap_hi, ap_lo, ...)
        nickname: 사용자 닉네임
        challenge_days: 챌린지 진행일

    Returns:
        통일된 응답 형식 (status, task_id, data, error)
    """
    task_id = self.request.id
    logger.info("ML1 분석 시작 - task_id: %s", task_id)

    try:
        result = ml1_run(user_data, nickname, challenge_days)

        # 캐시 저장
        cache_key = _build_cache_key(user_data, nickname, challenge_days)
        try:
            cache_redis.setex(cache_key, CACHE_TTL, json.dumps(result))
            logger.info("ML1 캐시 저장 완료 - key: %s", cache_key)
        except Exception as cache_err:
            logger.warning("ML1 캐시 저장 실패 (무시) - %s", cache_err)

        logger.info("ML1 분석 완료 - task_id: %s", task_id)
        return {
            "status": "success",
            "task_id": task_id,
            "data": result,
            "error": None,
        }

    except Exception as exc:
        logger.error("ML1 분석 실패 (retry 시도) - task_id: %s, error: %s", task_id, exc)
        raise self.retry(exc=exc)
