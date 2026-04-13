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
# Redis 클라이언트 설정
# DB 2: ML1 분석 결과 캐시 (24시간 TTL)
# DB 3: Pub/Sub 발행 (태스크 완료 실시간 알림)
# ──────────────────────────────────────────────
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_redis_base = REDIS_URL.rsplit("/", 1)[0]

CACHE_REDIS_URL = os.getenv("REDIS_CACHE_URL", _redis_base + "/2")
PUBSUB_REDIS_URL = os.getenv("REDIS_PUBSUB_URL", _redis_base + "/3")

cache_redis = redis.from_url(CACHE_REDIS_URL, decode_responses=True)
pubsub_redis = redis.from_url(PUBSUB_REDIS_URL, decode_responses=True)

# 캐시 TTL: 24시간
CACHE_TTL = 86400


def _publish_result(task_id: str, payload: dict) -> None:
    """태스크 완료 결과를 Redis Pub/Sub 채널에 발행한다."""
    channel = f"task:result:{task_id}"
    try:
        pubsub_redis.publish(channel, json.dumps(payload))
        logger.info("Pub/Sub 발행 완료 - channel: %s", channel)
    except Exception as pub_err:
        logger.warning("Pub/Sub 발행 실패 (무시) - %s", pub_err)


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
        logger.info("cache_key: %s", cache_key)
        try:
            cache_redis.setex(cache_key, CACHE_TTL, json.dumps(result))
            logger.info("ML1 캐시 저장 완료 - key: %s", cache_key)
        except Exception as cache_err:
            logger.warning("ML1 캐시 저장 실패 (무시) - %s", cache_err)

        result_payload = {
            "status": "success",
            "task_id": task_id,
            "data": result,
            "error": None,
        }

        # Pub/Sub 발행 (SSE 구독 중인 클라이언트에 실시간 전달)
        _publish_result(task_id, result_payload)

        logger.info("ML1 분석 완료 - task_id: %s", task_id)
        return result_payload

    except Exception as exc:
        logger.error("ML1 분석 실패 (retry 시도) - task_id: %s, error: %s", task_id, exc)
        raise self.retry(exc=exc) from exc
    
# ──────────────────────────────────────────────
# ML1 챌린지 달성 후 재계산 Celery Task
# ──────────────────────────────────────────────
@celery_app.task(
    name="ml1.recalculate_risk",
    bind=True,
    max_retries=2,
    default_retry_delay=5,
)
def recalculate_health(self, user_data: dict, completed_challenges: list, nickname: str = "사용자") -> dict:
    """
    챌린지 달성 후 위험도 재계산

    Args:
        user_data: 사용자 건강 데이터
        completed_challenges: ['smoke_7days', 'active_7days']
        nickname: 사용자 닉네임
    """
    from ai.workers.predict import recalculate_risk

    task_id = self.request.id
    logger.info("ML1 재계산 시작 - task_id: %s", task_id)

    try:
        result = recalculate_risk(user_data, completed_challenges)

        result_payload = {
            "status": "success",
            "task_id": task_id,
            "data": result,
            "error": None,
        }

        _publish_result(task_id, result_payload)
        logger.info("ML1 재계산 완료 - task_id: %s", task_id)
        return result_payload

    except Exception as exc:
        logger.error("ML1 재계산 실패 - task_id: %s, error: %s", task_id, exc)
        raise self.retry(exc=exc) from exc