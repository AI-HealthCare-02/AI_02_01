"""
AI Worker 통합 모듈
ML1: XGBoost 위험도 예측 + ChatGPT 건강 코멘트 생성
"""

import asyncio
import json
import logging
import os

from openai import OpenAI

from ai.workers.predict import predict, recalculate_risk  # noqa: F401
from ai.workers.prompt import SYSTEM_PROMPT, SYSTEM_PROMPT_RAG, build_user_prompt

logger = logging.getLogger(__name__)


# ── ML1 xgboost 함수 (XGBoost 예측)
def ml1_predict(user_data: dict) -> dict:
    """
    건강검진 수치 → 위험도 예측
    """
    return predict(user_data)


# ── ML1 LLM 코멘트 함수
def ml1_comment(user_info: dict, retrieved_context: str = "") -> dict:
    """
    위험도 결과 → 건강 코멘트 생성.
    Celery prefork 환경에서 fork-safety 문제 방지를 위해
    OpenAI 클라이언트를 함수 내부에서 생성.

    Args:
        user_info: ML1 예측 결과 + 사용자 기본 정보
        retrieved_context: RAG 검색 결과 텍스트 (빈 문자열이면 기본 프롬프트 사용)

    Langfuse 로깅:
    - LANGFUSE_PUBLIC_KEY가 설정된 경우에만 활성화
    - 미설정 환경에서는 기본 OpenAI 클라이언트로 폴백
    - Langfuse name: "ml1-health-comment" (RAG 미적용) / "ml1-health-comment-rag" (RAG 적용)
    """
    use_rag = bool(retrieved_context)
    langfuse_name = "ml1-health-comment-rag" if use_rag else "ml1-health-comment"

    langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    use_langfuse = False

    if langfuse_public_key:
        try:
            from langfuse.openai import openai as langfuse_openai

            client = langfuse_openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=60)
            use_langfuse = True
            logger.info("Langfuse 클라이언트 초기화 완료 (name=%s)", langfuse_name)
        except Exception as e:
            logger.warning("Langfuse 초기화 실패, 기본 OpenAI 클라이언트로 폴백 - %s", e)
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=60)
    else:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=60)
        logger.info("Langfuse 미설정, 기본 OpenAI 클라이언트 사용")

    system_prompt = SYSTEM_PROMPT_RAG if use_rag else SYSTEM_PROMPT
    user_prompt = build_user_prompt(user_info, retrieved_context)

    logger.info("OpenAI API 호출 시작 (name=%s)", langfuse_name)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
        timeout=60,
        name=langfuse_name,
    )
    logger.info(
        "OpenAI API 호출 완료 (name=%s) - prompt_tokens=%s, completion_tokens=%s, total_tokens=%s",
        langfuse_name,
        response.usage.prompt_tokens if response.usage else "?",
        response.usage.completion_tokens if response.usage else "?",
        response.usage.total_tokens if response.usage else "?",
    )

    raw = response.choices[0].message.content

    if use_langfuse:
        try:
            from langfuse import Langfuse

            Langfuse().flush()
        except Exception:
            pass

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "evaluation": "건강 데이터를 분석했습니다.",
            "alert": None,
            "missions": [],
            "encouragement": "오늘도 건강한 하루 보내세요!",
        }


# ── ML1 통합 실행 함수
def ml1_run(
    user_data: dict,
    nickname: str = "사용자",
    challenge_days: int = 0,
) -> dict:
    """
    건강검진 수치 입력 → XGBoost 예측 + ChatGPT 코멘트 생성

    Args:
        user_data: 건강검진 수치
        nickname: 사용자 닉네임
        challenge_days: 챌린지 진행일

    Returns:
        {
            "ml1_predict": 위험도 예측 결과,
            "ml1_comment": 건강 코멘트
        }
    """
    # 1. ML xgboost 예측
    logger.info("XGBoost 예측 함수 호출 시작")
    predict_result = ml1_predict(user_data)
    logger.info("XGBoost 예측 함수 호출 완료")

    # 2. ML1 LLM 코멘트 생성
    user_info = {
        "nickname": nickname,
        "age": user_data["age"],
        "risk_percent": predict_result["risk_percent"],
        "risk_grade": predict_result["risk_grade"],
        "heart_age": predict_result["heart_age"],
        "top_risk_factors": predict_result["top_risk_factors"],
        "smoke": user_data["smoke"],
        "alco": user_data["alco"],
        "challenge_days": challenge_days,
    }
    logger.info("OpenAI 코멘트 생성 시작")
    comment_result = ml1_comment(user_info)
    logger.info("OpenAI 코멘트 생성 완료")

    return {
        "ml1_predict": predict_result,
        "ml1_comment": comment_result,
    }


# ── 테스트
if __name__ == "__main__":
    sample = {
        "age": 45,
        "gender": 1,
        "height": 165,
        "weight": 70,
        "ap_hi": 140,
        "ap_lo": 90,
        "cholesterol": 2,
        "gluc": 1,
        "smoke": 1,
        "alco": 0,
        "active": 0,
    }

    result = asyncio.run(ml1_run(sample, nickname="건강이", challenge_days=3))

    print("=== ML1 XGBoost 결과 ===")
    for k, v in result["ml1_predict"].items():
        print(f"{k}: {v}")

    print("\n=== ML1 LLM 결과 ===")
    for k, v in result["ml1_comment"].items():
        print(f"{k}: {v}")
