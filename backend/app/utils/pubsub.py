"""
Redis Pub/Sub 롱 폴링 유틸리티

역할: AI Worker가 발행한 태스크 완료 결과를 롱 폴링 방식으로 반환
채널 형식: task:result:{task_id}
DB: Redis DB 3 (Pub/Sub 전용)

흐름:
  [클라이언트] GET /tasks/{task_id}/wait 요청
      → [FastAPI] Redis Pub/Sub 채널 구독 후 대기
      → [AI Worker] 태스크 완료 → PUBLISH task:result:{task_id} {...}
      → [FastAPI] 메시지 수신 → 즉시 JSON 응답 반환 → 연결 종료
      → [클라이언트] 결과 수신 완료 (1회 요청으로 끝)

타임아웃 처리:
  - asyncio.timeout()으로 강제 타임아웃 적용 (기본 30초)
  - 메시지가 없어도 시간 초과 시 확실히 반환됨
  - 클라이언트는 pending 수신 시 즉시 재요청

Note:
  Redis Pub/Sub 채널은 DB 번호와 무관하게 서버 전역으로 공유된다.
  DB 3 연결은 논리적 분리를 위한 구성이다.
"""

import asyncio
import json
import logging

import redis.asyncio as aioredis

from app.core.config import Config

logger = logging.getLogger(__name__)

_config = Config()

# 롱 폴링 최대 대기 시간 (AI 분석 평균 처리 시간 고려)
LONG_POLL_TIMEOUT_SECONDS = 30

# 채널 접두어
CHANNEL_PREFIX = "task:result"


def build_channel(task_id: str) -> str:
    """태스크 ID에 해당하는 Pub/Sub 채널 이름을 반환한다."""
    return f"{CHANNEL_PREFIX}:{task_id}"


async def _listen_once(pubsub: aioredis.client.PubSub) -> dict:
    """
    Pub/Sub 채널에서 실제 데이터 메시지 1건을 수신할 때까지 대기한다.

    subscribe 확인 메시지는 무시하고, type="message"인 첫 번째 메시지를 반환한다.
    외부에서 asyncio.timeout()으로 감싸서 타임아웃을 제어해야 한다.
    """
    async for message in pubsub.listen():
        if message["type"] == "message":
            return json.loads(message["data"])
    return {}


async def wait_task_result(task_id: str, timeout: int = LONG_POLL_TIMEOUT_SECONDS) -> dict | None:
    """
    Redis Pub/Sub 채널을 구독하여 태스크 완료 결과를 최대 timeout초 대기 후 반환한다.

    롱 폴링 방식:
      - 서버가 결과가 올 때까지 응답을 보류 (최대 timeout초)
      - 결과 도착 즉시 반환 → HTTP 연결 종료
      - 타임아웃 시 None 반환 → 라우터에서 pending 응답

    타임아웃 처리:
      asyncio.timeout()으로 강제 타임아웃 적용.
      pubsub.listen()은 메시지 수신 시에만 제어가 반환되므로,
      메시지 없이 시간이 초과되면 asyncio가 강제로 취소(CancelledError)하여
      반드시 timeout초 이내에 함수가 종료된다.

    Args:
        task_id: Celery 태스크 ID
        timeout: 최대 대기 시간 (초), 기본 30초

    Returns:
        dict: 태스크 결과 payload (완료 시)
        None: 타임아웃 또는 오류 시
    """
    channel = build_channel(task_id)
    redis_client = aioredis.from_url(_config.REDIS_PUBSUB_URL, decode_responses=True)
    pubsub = redis_client.pubsub()

    try:
        await pubsub.subscribe(channel)
        logger.info("롱 폴링 구독 시작 - channel: %s, timeout: %ds", channel, timeout)

        # asyncio.timeout()으로 강제 타임아웃 적용
        # pubsub.listen()이 무한 대기하더라도 timeout초 후 TimeoutError 발생
        async with asyncio.timeout(timeout):
            result = await _listen_once(pubsub)
            logger.info("롱 폴링 결과 수신 - channel: %s", channel)
            return result

    except TimeoutError:
        # asyncio.timeout() 초과 시 발생 (Python 3.11+)
        logger.warning("롱 폴링 타임아웃 - channel: %s, %d초 초과", channel, timeout)
        return None

    except Exception as exc:
        logger.error("롱 폴링 오류 - channel: %s, error: %s", channel, exc)
        return None

    finally:
        await pubsub.unsubscribe(channel)
        await redis_client.aclose()
        logger.info("롱 폴링 구독 해제 - channel: %s", channel)
