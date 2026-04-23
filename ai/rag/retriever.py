"""
RAG 검색 파이프라인
쿼리 → 임베딩 → Qdrant 유사도 검색 → LLM 프롬프트용 컨텍스트 반환
"""

import logging
from dataclasses import dataclass

from qdrant_client.http.models import FieldCondition, Filter, MatchValue

from ai.core.embeddings import embed, embed_async
from ai.core.vector_store import get_qdrant_client

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    text: str
    score: float
    source: str
    category: str
    topic: str


def retrieve_health_context(
    query: str,
    risk_grade: str,
    top_k: int | None = None,
    min_score: float | None = None,
    collection: str | None = None,
) -> list[RetrievedChunk]:
    """
    동기 버전 — Celery 워커에서 사용.

    Args:
        query:      검색 쿼리 (사용자 위험 요인, 건강 상태 요약 텍스트)
        risk_grade: 사용자 위험 등급 ("낮음" | "보통" | "중간" | "높음" | "매우높음")
        top_k:      반환할 최대 문서 수 (None이면 config.RAG_TOP_K 사용)
        min_score:  최소 유사도 임계값 (None이면 config.RAG_MIN_SCORE 사용)
        collection: Qdrant 컬렉션명 (None이면 config.QDRANT_COLLECTION_MEDICAL 사용)

    Returns:
        유사도 내림차순 정렬된 RetrievedChunk 리스트
    """
    from ai.core import config

    top_k = top_k or config.RAG_TOP_K
    min_score = min_score or config.RAG_MIN_SCORE
    collection = collection or config.QDRANT_COLLECTION_MEDICAL

    query_vector = embed(query)
    return _search(query_vector, risk_grade, top_k, min_score, collection)


async def retrieve_health_context_async(
    query: str,
    risk_grade: str,
    top_k: int | None = None,
    min_score: float | None = None,
    collection: str | None = None,
) -> list[RetrievedChunk]:
    """비동기 버전 — FastAPI 엔드포인트에서 사용."""
    from ai.core import config

    top_k = top_k or config.RAG_TOP_K
    min_score = min_score or config.RAG_MIN_SCORE
    collection = collection or config.QDRANT_COLLECTION_MEDICAL

    query_vector = await embed_async(query)
    return _search(query_vector, risk_grade, top_k, min_score, collection)


def _search(
    query_vector: list[float],
    risk_grade: str,
    top_k: int,
    min_score: float,
    collection: str,
) -> list[RetrievedChunk]:
    """Qdrant 검색 공통 로직."""
    client = get_qdrant_client()

    # risk_grade가 있으면 해당 등급 문서만 필터링, 없으면 전체 검색
    query_filter = (
        Filter(
            must=[FieldCondition(key="risk_grades", match=MatchValue(value=risk_grade))]
        )
        if risk_grade
        else None
    )

    response = client.query_points(
        collection_name=collection,
        query=query_vector,
        query_filter=query_filter,
        limit=top_k,
        score_threshold=min_score,
        with_payload=True,
    )

    chunks = [
        RetrievedChunk(
            text=r.payload.get("text", ""),
            score=r.score,
            source=r.payload.get("source", ""),
            category=r.payload.get("category", ""),
            topic=r.payload.get("topic", ""),
        )
        for r in response.points
    ]

    logger.info(
        "RAG 검색 완료: collection=%s, risk_grade=%s, 결과=%d개 (top_k=%d, min_score=%.2f)",
        collection,
        risk_grade,
        len(chunks),
        top_k,
        min_score,
    )
    return chunks


def format_context_for_prompt(chunks: list[RetrievedChunk]) -> str:
    """
    검색된 청크 리스트 → LLM 프롬프트 삽입용 텍스트 포맷팅.

    빈 리스트가 들어오면 빈 문자열 반환.
    """
    if not chunks:
        return ""

    lines = []
    for i, chunk in enumerate(chunks, 1):
        lines.append(f"[참고 {i}] (출처: {chunk.source}, 유사도: {chunk.score:.2f})")
        lines.append(chunk.text)
        lines.append("")  # 청크 간 빈 줄 구분

    return "\n".join(lines).strip()


def build_nutrition_rag_query(risk_grade: str, risk_factors: str = "") -> str:
    """
    Vision API 식단 분석용 RAG 쿼리 생성.

    식단 분석에서는 사용자 위험도 및 위험 요인을 기반으로
    관련 영양 가이드라인을 검색한다.
    """
    parts = [f"심혈관 위험도 {risk_grade} 환자 식이 가이드라인"]

    if risk_factors:
        parts.append(f"주요 위험 요인: {risk_factors}")
        # 위험 요인 키워드에서 질환별 식이 힌트 추가
        if "고혈압" in risk_factors or "혈압" in risk_factors:
            parts.append("나트륨 제한 DASH 식이 혈압 관리")
        if "당뇨" in risk_factors or "혈당" in risk_factors:
            parts.append("혈당 지수 탄수화물 제한 식이섬유")
        if "콜레스테롤" in risk_factors or "고지혈" in risk_factors:
            parts.append("포화지방 오메가-3 식이섬유 LDL 관리")

    parts.append("한국인 균형 식사 한 끼 영양소 구성")

    return ". ".join(parts)


def build_rag_query(user_info: dict) -> str:
    """
    ML1 사용자 정보 dict → RAG 검색 쿼리 텍스트 생성.

    위험 요인을 자연어로 변환하여 의미 검색 품질 향상.
    """
    risk_grade = user_info.get("risk_grade", "")
    factors = user_info.get("top_risk_factors", [])
    age = user_info.get("age", "")
    smoke = user_info.get("smoke", 0)
    alco = user_info.get("alco", 0)

    parts = [f"심혈관 위험도 {risk_grade}"]

    if factors:
        parts.append(f"주요 위험 요인: {', '.join(factors)}")

    if age:
        parts.append(f"{age}세 환자")

    if smoke:
        parts.append("흡연자 금연 지도")

    if alco:
        parts.append("음주자 절주 지도")

    parts.append("생활습관 개선 방법 및 의학 가이드라인")

    return ". ".join(parts)
