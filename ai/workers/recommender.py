"""
RAG 기반 챌린지 추천 모듈

흐름:
  1. embed_challenges(): 챌린지 목록 → OpenAI 임베딩 → Redis 저장
  2. recommend(): 유저 프로필 임베딩 → 코사인 유사도 → Top K 추출 → GPT 이유 생성
"""

import json
import logging
import math
import os

import redis
from openai import OpenAI
logger = logging.getLogger(__name__)

_broker = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
_redis_base = _broker.rsplit("/", 1)[0]
EMBED_REDIS_URL = os.getenv("REDIS_EMBED_URL", _redis_base + "/4")

embed_redis = redis.from_url(EMBED_REDIS_URL, decode_responses=True)

EMBED_MODEL = "text-embedding-3-small"
EMBED_TTL = 60 * 60 * 24 * 30  # 30일
TOP_K = 5


def _get_client() -> OpenAI:
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=60)

def _embed(text: str, client: OpenAI) -> list[float]:
    """텍스트 → 임베딩 벡터 (Langfuse name: ml1-embedding-challenge)"""
    response = client.embeddings.create(model=EMBED_MODEL, input=text, name="ml1-embedding-challenge")
    logger.info(
        "임베딩 완료 (name=ml1-embedding-challenge) - total_tokens=%s",
        response.usage.total_tokens if response.usage else "?",
    )
    return response.data[0].embedding


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """두 벡터의 코사인 유사도 계산"""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _challenge_to_text(challenge: dict) -> str:
    """챌린지 dict → 임베딩용 텍스트"""
    return (
        f"{challenge['title']}. "
        f"카테고리: {challenge.get('category', '')}. "
        f"대상 위험 요인: {challenge.get('target_risk_factors', '')}. "
        f"기대 효과: {challenge.get('expected_effect', '')}. "
        f"{challenge.get('description', '')}"
    )


def _user_to_text(user_profile: dict, prediction: dict) -> str:
    """유저 건강 프로필 → 임베딩용 텍스트"""
    risk_factors = ", ".join(prediction.get("top_risk_factors", []))
    gender = "여성" if user_profile.get("gender") == "F" else "남성"
    return (
        f"{user_profile.get('age', '')}세 {gender}. "
        f"심혈관 위험도: {prediction.get('risk_level', '')}. "
        f"주요 위험 요인: {risk_factors}. "
        f"심혈관 나이: {prediction.get('cvd_age', '')}세."
    )


def embed_and_store_challenges(challenges: list[dict]) -> int:
    """
    챌린지 목록을 임베딩하여 Redis DB4에 저장.
    이미 저장된 챌린지는 스킵.
    Returns: 새로 임베딩한 챌린지 수
    """
    client = _get_client()
    new_count = 0

    for challenge in challenges:
        key = f"challenge:embed:{challenge['id']}"
        if embed_redis.exists(key):
            continue

        text = _challenge_to_text(challenge)
        vector = _embed(text, client)
        embed_redis.setex(key, EMBED_TTL, json.dumps(vector))
        new_count += 1
        logger.info("챌린지 임베딩 저장 - id: %d, title: %s", challenge["id"], challenge["title"])

    return new_count


def retrieve_top_k(user_profile: dict, prediction: dict, challenges: list[dict]) -> list[dict]:
    """
    유저 프로필 임베딩 → 챌린지와 코사인 유사도 계산 → Top K 반환
    Redis에 임베딩이 없는 챌린지는 실시간 임베딩
    """
    client = _get_client()
    user_text = _user_to_text(user_profile, prediction)
    user_vector = _embed(user_text, client)

    scored = []
    for challenge in challenges:
        key = f"challenge:embed:{challenge['id']}"
        raw = embed_redis.get(key)
        if raw:
            challenge_vector = json.loads(raw)
        else:
            challenge_vector = _embed(_challenge_to_text(challenge), client)
            embed_redis.setex(key, EMBED_TTL, json.dumps(challenge_vector))

        score = _cosine_similarity(user_vector, challenge_vector)
        scored.append((score, challenge))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:TOP_K]]


def _get_langfuse_client() -> tuple[OpenAI, bool]:
    """
    Langfuse 설정 여부에 따라 클라이언트 반환.
    Returns: (client, use_langfuse)
    """
    langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    if langfuse_public_key:
        try:
            from langfuse.openai import openai as langfuse_openai
            return langfuse_openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=60), True
        except Exception as e:
            logger.warning("Langfuse 초기화 실패, 기본 OpenAI 클라이언트로 폴백 - %s", e)
    return _get_client(), False


def _flush_langfuse() -> None:
    """Langfuse 버퍼 플러시."""
    try:
        from langfuse import Langfuse
        Langfuse().flush()
    except Exception:
        pass


def generate_recommendations(
    user_profile: dict,
    prediction: dict,
    top_challenges: list[dict],
) -> list[dict]:
    """
    Top K 챌린지 + 유저 데이터 → GPT → 추천 이유 포함 Top 3 반환
    Langfuse name: "ml1-challenge-recommend"
    """
    langfuse_name = "ml1-challenge-recommend"
    client, use_langfuse = _get_langfuse_client()

    challenge_list_text = "\n".join([
        f"[ID:{c['id']}] {c['title']} | 카테고리:{c.get('category','')} | "
        f"대상위험요인:{c.get('target_risk_factors','')} | 기대효과:{c.get('expected_effect','')}"
        for c in top_challenges
    ])

    system_prompt = (
        "당신은 심혈관 건강 전문 AI 코치입니다.\n"
        "아래 챌린지 후보 중 사용자에게 가장 적합한 3개를 선택하고 추천 이유를 작성하세요.\n\n"
        "[규칙]\n"
        "1. 반드시 JSON 형식으로만 응답하세요.\n"
        "2. JSON 외 텍스트 포함 금지.\n"
        "3. challenge_id는 반드시 제공된 목록의 ID를 사용하세요.\n"
        "4. reason은 사용자의 건강 상태와 연결된 친근하고 구체적인 이유를 2문장으로 작성하세요.\n"
        "5. 정확히 3개 추천 (후보가 3개 미만이면 전체).\n\n"
        '[응답 형식]\n{"recommendations":[{"challenge_id":1,"title":"제목","reason":"이유"}]}'
    )

    risk_factors = ", ".join(prediction.get("top_risk_factors", []))
    gender = "여성" if user_profile.get("gender") == "F" else "남성"

    user_prompt = (
        f"닉네임: {user_profile.get('nickname', '사용자')}\n"
        f"나이: {user_profile.get('age', '-')}세 / 성별: {gender}\n"
        f"심혈관 위험도: {prediction.get('risk_percent', '-')}% ({prediction.get('risk_level', '-')})\n"
        f"심혈관 나이: {prediction.get('cvd_age', '-')}세\n"
        f"주요 위험 요인: {risk_factors}\n\n"
        f"[챌린지 후보]\n{challenge_list_text}"
    )

    logger.info("OpenAI API 호출 시작 (name=%s)", langfuse_name)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
        name=langfuse_name,
    )
    logger.info(
        "OpenAI API 호출 완료 (name=%s) - prompt_tokens=%s, completion_tokens=%s, total_tokens=%s",
        langfuse_name,
        response.usage.prompt_tokens if response.usage else "?",
        response.usage.completion_tokens if response.usage else "?",
        response.usage.total_tokens if response.usage else "?",
    )

    if use_langfuse:
        _flush_langfuse()

    raw = response.choices[0].message.content
    try:
        parsed = json.loads(raw)
        return parsed.get("recommendations", [])
    except json.JSONDecodeError:
        logger.error("GPT 응답 JSON 파싱 실패 - raw: %s", raw)
        return []
