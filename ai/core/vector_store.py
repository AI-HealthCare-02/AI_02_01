"""
Qdrant Vector DB 클라이언트 싱글톤
"""

import logging

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

logger = logging.getLogger(__name__)

_client: QdrantClient | None = None

# OpenAI text-embedding-3-small 벡터 차원
EMBEDDING_DIM = 1536


def get_qdrant_client() -> QdrantClient:
    """Qdrant 클라이언트 싱글톤 반환."""
    global _client
    if _client is None:
        from ai.core import config

        _client = QdrantClient(
            host=config.QDRANT_HOST,
            port=config.QDRANT_PORT,
            api_key=config.QDRANT_API_KEY or None,
            # API 키가 있어도 로컬 Docker는 SSL 미사용이므로 명시적으로 비활성화
            https=False,
            timeout=10,
        )
        logger.info("Qdrant 클라이언트 초기화 완료 (%s:%s)", config.QDRANT_HOST, config.QDRANT_PORT)
    return _client


def ensure_collection(collection_name: str) -> None:
    """컬렉션이 없으면 생성."""
    client = get_qdrant_client()
    existing = {c.name for c in client.get_collections().collections}
    if collection_name not in existing:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
        logger.info("Qdrant 컬렉션 생성: %s", collection_name)
    else:
        logger.debug("Qdrant 컬렉션 이미 존재: %s", collection_name)
