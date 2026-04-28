"""
RAG 문서 인덱서
의학·영양 지식 문서 → 청킹 → 임베딩 → Qdrant 적재
"""

import asyncio
import hashlib
import logging
import re
import uuid
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client.http.models import PointStruct

from ai.core.embeddings import embed_batch_async
from ai.core.vector_store import EMBEDDING_DIM, ensure_collection, get_qdrant_client

logger = logging.getLogger(__name__)

DOCS_DIR = Path(__file__).parent / "documents"
NUTRITION_DOCS_DIR = Path(__file__).parent / "documents_nutrition"

# 청킹 설정 (Notion 계획 기준)
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n## ", "\n### ", "\n\n", "\n", "。", ". ", " "],
)

# YAML 프론트매터 파싱 정규식
_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
_FIELD_RE = re.compile(r"^(\w+):\s*(.+)$", re.MULTILINE)
_LIST_RE = re.compile(r"\[(.+?)\]")


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """YAML 프론트매터 파싱 → (메타데이터 dict, 본문 str)."""
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return {}, content

    meta: dict = {}
    for key, value in _FIELD_RE.findall(match.group(1)):
        list_match = _LIST_RE.match(value.strip())
        if list_match:
            meta[key] = [v.strip() for v in list_match.group(1).split(",")]
        else:
            meta[key] = value.strip()

    body = content[match.end() :]
    return meta, body


def _load_documents(docs_dir: Path) -> list[dict]:
    """문서 디렉토리 순회 → 파싱된 문서 리스트 반환."""
    documents = []
    for md_file in sorted(docs_dir.rglob("*.md")):
        raw = md_file.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(raw)
        documents.append(
            {
                "file": md_file.stem,
                "meta": meta,
                "body": body,
            }
        )
        logger.debug("문서 로드: %s", md_file.relative_to(docs_dir))

    logger.info("총 %d개 문서 로드 완료", len(documents))
    return documents


def _chunk_documents(documents: list[dict]) -> list[dict]:
    """문서 → 청크 리스트 생성."""
    chunks = []
    for doc in documents:
        parts = _splitter.split_text(doc["body"])
        for i, text in enumerate(parts):
            text = text.strip()
            if len(text) < 30:  # 너무 짧은 청크 제외
                continue
            # 파일명 + 청크 인덱스 기반 결정적 ID: 재실행 시 upsert(중복 없음)
            chunk_hash = hashlib.md5(f"{doc['file']}:{i}".encode()).hexdigest()
            chunk_id = str(uuid.UUID(chunk_hash))
            chunks.append(
                {
                    "id": chunk_id,
                    "text": text,
                    "metadata": {
                        "source": doc["file"],
                        "category": doc["meta"].get("category", "unknown"),
                        "topic": doc["meta"].get("topic", "general"),
                        "risk_grades": doc["meta"].get("risk_grades", []),
                        "chunk_index": i,
                    },
                }
            )
    logger.info("총 %d개 청크 생성 완료", len(chunks))
    return chunks


async def _upsert_chunks(collection: str, chunks: list[dict], batch_size: int = 50) -> None:
    """청크 배치 임베딩 → Qdrant upsert."""
    client = get_qdrant_client()
    ensure_collection(collection)

    total = len(chunks)
    for start in range(0, total, batch_size):
        batch = chunks[start : start + batch_size]
        texts = [c["text"] for c in batch]

        logger.info("임베딩 요청 중 (%d/%d)...", min(start + batch_size, total), total)
        vectors = await embed_batch_async(texts)

        points = [
            PointStruct(
                id=chunk["id"],
                vector=vector,
                payload={
                    "text": chunk["text"],
                    **chunk["metadata"],
                },
            )
            for chunk, vector in zip(batch, vectors, strict=True)
        ]

        client.upsert(collection_name=collection, points=points, wait=True)
        logger.info("Qdrant upsert 완료: %d개 포인트", len(points))


async def index_medical_knowledge(force: bool = False) -> int:
    """
    medical_knowledge 컬렉션에 의학·운동·영양 문서 전체 인덱싱.

    Args:
        force: True이면 기존 컬렉션을 삭제하고 재인덱싱

    Returns:
        삽입된 총 청크 수
    """
    from ai.core import config

    collection = config.QDRANT_COLLECTION_MEDICAL

    if force:
        client = get_qdrant_client()
        existing = {c.name for c in client.get_collections().collections}
        if collection in existing:
            client.delete_collection(collection)
            logger.info("기존 컬렉션 삭제: %s", collection)

    documents = _load_documents(DOCS_DIR)
    chunks = _chunk_documents(documents)
    await _upsert_chunks(collection, chunks)

    logger.info("인덱싱 완료: 컬렉션=%s, 청크=%d개", collection, len(chunks))
    return len(chunks)


async def index_nutrition_knowledge(force: bool = False) -> int:
    """
    nutrition_knowledge 컬렉션에 영양·식이 가이드 문서 전체 인덱싱.

    Args:
        force: True이면 기존 컬렉션을 삭제하고 재인덱싱

    Returns:
        삽입된 총 청크 수
    """
    from ai.core import config

    collection = config.QDRANT_COLLECTION_NUTRITION

    if force:
        client = get_qdrant_client()
        existing = {c.name for c in client.get_collections().collections}
        if collection in existing:
            client.delete_collection(collection)
            logger.info("기존 컬렉션 삭제: %s", collection)

    documents = _load_documents(NUTRITION_DOCS_DIR)
    chunks = _chunk_documents(documents)
    await _upsert_chunks(collection, chunks)

    logger.info("인덱싱 완료: 컬렉션=%s, 청크=%d개", collection, len(chunks))
    return len(chunks)


def _print_collection_stats() -> None:
    """컬렉션 통계 출력 (검증용)."""
    from ai.core import config

    client = get_qdrant_client()
    for name in [config.QDRANT_COLLECTION_MEDICAL, config.QDRANT_COLLECTION_NUTRITION]:
        try:
            info = client.get_collection(name)
            points = info.points_count or info.vectors_count or 0
            print(f"\n[{name}]")
            print(f"  포인트 수: {points}")
            print(f"  차원: {EMBEDDING_DIM}")
        except Exception:
            print(f"\n[{name}] 컬렉션 없음")


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv

    # 호스트에서 직접 실행 시 .env 로드 (Celery 환경에서는 불필요)
    load_dotenv()

    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    force = "--force" in sys.argv

    total_medical = asyncio.run(index_medical_knowledge(force=force))
    print(f"\n[medical_knowledge] 인덱싱 완료: 총 {total_medical}개 청크")

    total_nutrition = asyncio.run(index_nutrition_knowledge(force=force))
    print(f"[nutrition_knowledge] 인덱싱 완료: 총 {total_nutrition}개 청크")

    _print_collection_stats()
