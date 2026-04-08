"""
Redis 비동기 클라이언트 모듈

역할: ML1 분석 결과 캐싱용 Redis 연결 관리
DB 분리: DB 1번 (Celery broker는 DB 0번 사용)
"""

import logging

import redis.asyncio as aioredis

from app.core.config import Config

logger = logging.getLogger(__name__)

# 모듈 레벨 싱글턴 Redis 클라이언트
_redis_client: aioredis.Redis | None = None

config = Config()


async def init_redis() -> None:
    """Redis 연결 초기화 (서버 시작 시 호출)"""
    global _redis_client
    _redis_client = aioredis.from_url(
        config.REDIS_URL,
        decode_responses=True,
    )
    logger.info("Redis 연결 초기화 완료 - %s", config.REDIS_URL)


async def close_redis() -> None:
    """Redis 연결 해제 (서버 종료 시 호출)"""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("Redis 연결 해제 완료")


def get_redis() -> aioredis.Redis:
    """Redis 클라이언트 반환 (초기화되지 않았으면 에러)"""
    if _redis_client is None:
        raise RuntimeError("Redis 클라이언트가 초기화되지 않았습니다. init_redis()를 먼저 호출하세요.")
    return _redis_client
