"""
OpenAI Embedding 클라이언트
text-embedding-3-small 모델 사용 (1536차원, 한국어 양호)
"""

import logging
import os

from openai import AsyncOpenAI, OpenAI

logger = logging.getLogger(__name__)

_async_client: AsyncOpenAI | None = None
_sync_client: OpenAI | None = None

EMBEDDING_MODEL = "text-embedding-3-small"


def get_embedding_client() -> OpenAI:
    """동기 OpenAI 클라이언트 반환 (Celery 워커용)."""
    global _sync_client
    if _sync_client is None:
        _sync_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=30)
        logger.info("OpenAI 동기 Embedding 클라이언트 초기화 완료")
    return _sync_client


def get_async_embedding_client() -> AsyncOpenAI:
    """비동기 OpenAI 클라이언트 반환 (FastAPI / 인덱서용)."""
    global _async_client
    if _async_client is None:
        _async_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=30)
        logger.info("OpenAI 비동기 Embedding 클라이언트 초기화 완료")
    return _async_client


def embed(text: str) -> list[float]:
    """텍스트 → 임베딩 벡터 (동기)."""
    client = get_embedding_client()
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding


async def embed_async(text: str) -> list[float]:
    """텍스트 → 임베딩 벡터 (비동기)."""
    client = get_async_embedding_client()
    response = await client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding


async def embed_batch_async(texts: list[str]) -> list[list[float]]:
    """텍스트 리스트 → 임베딩 벡터 리스트 (비동기 배치)."""
    client = get_async_embedding_client()
    response = await client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    # API 응답은 index 순서 보장
    sorted_data = sorted(response.data, key=lambda d: d.index)
    logger.info("배치 임베딩 완료: %d개 텍스트", len(texts))
    return [d.embedding for d in sorted_data]
