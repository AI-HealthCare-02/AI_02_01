"""
OpenAI Embedding 클라이언트
text-embedding-3-small 모델 사용 (1536차원, 한국어 양호)

Langfuse name 규칙:
  - ml1-embedding-rag      : RAG 검색 쿼리 임베딩 (동기, Celery 워커)
  - ml1-embedding-rag-batch: RAG 문서 인덱싱 배치 임베딩 (비동기, 인덱서)
  - ml1-embedding-challenge: 챌린지 추천용 임베딩 (recommender.py에서 직접 호출)
"""

import logging
import os

from openai import AsyncOpenAI, OpenAI

logger = logging.getLogger(__name__)

_async_client: AsyncOpenAI | None = None
_sync_client: OpenAI | None = None

EMBEDDING_MODEL = "text-embedding-3-small"


def _get_langfuse_sync_client() -> tuple[OpenAI, bool]:
    """Langfuse 설정 여부에 따라 동기 클라이언트 반환."""
    if os.getenv("LANGFUSE_PUBLIC_KEY"):
        try:
            from langfuse.openai import openai as langfuse_openai
            return langfuse_openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=30), True
        except Exception as e:
            logger.warning("Langfuse 동기 클라이언트 초기화 실패, 폴백 - %s", e)
    return get_embedding_client(), False


def _get_langfuse_async_client() -> tuple[AsyncOpenAI, bool]:
    """Langfuse 설정 여부에 따라 비동기 클라이언트 반환."""
    if os.getenv("LANGFUSE_PUBLIC_KEY"):
        try:
            from langfuse.openai import openai as langfuse_openai
            return langfuse_openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=30), True
        except Exception as e:
            logger.warning("Langfuse 비동기 클라이언트 초기화 실패, 폴백 - %s", e)
    return get_async_embedding_client(), False


def _flush_langfuse() -> None:
    try:
        from langfuse import Langfuse
        Langfuse().flush()
    except Exception:
        pass


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


def embed(text: str, langfuse_name: str = "ml1-embedding-rag") -> list[float]:
    """텍스트 → 임베딩 벡터 (동기).

    Args:
        text: 임베딩할 텍스트
        langfuse_name: Langfuse에서 구분할 name (기본: ml1-embedding-rag)
    """
    client, use_langfuse = _get_langfuse_sync_client()
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=text, name=langfuse_name)
    logger.info(
        "임베딩 완료 (name=%s) - total_tokens=%s",
        langfuse_name,
        response.usage.total_tokens if response.usage else "?",
    )
    if use_langfuse:
        _flush_langfuse()
    return response.data[0].embedding


async def embed_async(text: str, langfuse_name: str = "ml1-embedding-rag") -> list[float]:
    """텍스트 → 임베딩 벡터 (비동기).

    Args:
        text: 임베딩할 텍스트
        langfuse_name: Langfuse에서 구분할 name (기본: ml1-embedding-rag)
    """
    client, use_langfuse = _get_langfuse_async_client()
    response = await client.embeddings.create(model=EMBEDDING_MODEL, input=text, name=langfuse_name)
    logger.info(
        "임베딩 완료 (name=%s) - total_tokens=%s",
        langfuse_name,
        response.usage.total_tokens if response.usage else "?",
    )
    if use_langfuse:
        _flush_langfuse()
    return response.data[0].embedding


async def embed_batch_async(texts: list[str], langfuse_name: str = "ml1-embedding-rag-batch") -> list[list[float]]:
    """텍스트 리스트 → 임베딩 벡터 리스트 (비동기 배치).

    Args:
        texts: 임베딩할 텍스트 리스트
        langfuse_name: Langfuse에서 구분할 name (기본: ml1-embedding-rag-batch)
    """
    client, use_langfuse = _get_langfuse_async_client()
    response = await client.embeddings.create(model=EMBEDDING_MODEL, input=texts, name=langfuse_name)
    sorted_data = sorted(response.data, key=lambda d: d.index)
    logger.info(
        "배치 임베딩 완료 (name=%s) - %d개 텍스트, total_tokens=%s",
        langfuse_name,
        len(texts),
        response.usage.total_tokens if response.usage else "?",
    )
    if use_langfuse:
        _flush_langfuse()
    return [d.embedding for d in sorted_data]
