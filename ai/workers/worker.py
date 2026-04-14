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
from ai.workers.prompt import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)


# ── ML1 xgboost 함수 (XGBoost 예측)
def ml1_predict(user_data: dict) -> dict:
    """
    건강검진 수치 → 위험도 예측
    """
    return predict(user_data)


# ── ML1 LLM 코멘트 함수
def ml1_comment(user_info: dict) -> dict:
    """
    위험도 결과 → 건강 코멘트 생성.
    Celery prefork 환경에서 fork-safety 문제 방지를 위해
    OpenAI 클라이언트를 함수 내부에서 생성.

    Langfuse 로깅:
    - LANGFUSE_PUBLIC_KEY가 설정된 경우(로컬 Docker)에만 활성화
    - EC2 등 Langfuse 미설치 환경에서는 기본 OpenAI 클라이언트로 폴백
    """
    # fork된 워커 프로세스마다 독립적인 클라이언트 인스턴스 생성
    # Langfuse 설정 여부에 따라 클라이언트 선택
    langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    if langfuse_public_key:
        logger.info("Langfuse 설정")
        try:
            from langfuse import Langfuse
            from langfuse.openai import openai as langfuse_openai

            # LANGFUSE_HOST 또는 LANGFUSE_BASE_URL 둘 다 지원
            langfuse_host = os.getenv("LANGFUSE_HOST") or os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")
            langfuse = Langfuse(
                public_key=langfuse_public_key,
                secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                host=langfuse_host,
            )
            client = langfuse_openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=60)
            use_langfuse = True
            logger.info("Langfuse 클라이언트 초기화 완료 - host: %s", langfuse_host)
        except Exception as e:
            logger.warning("Langfuse 초기화 실패, 기본 OpenAI 클라이언트로 폴백 - %s", e)
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            use_langfuse = False
            langfuse = None
    else:
        logger.info("Langfuse 미설정, 기본 OpenAI 클라이언트 사용")
        # Langfuse 미설정 환경 (EC2 등): 기본 OpenAI 클라이언트 사용
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        use_langfuse = False
        langfuse = None

    user_prompt = build_user_prompt(user_info)

    logger.info("OpenAI API 호출 시작")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
        timeout=60,
    )
    logger.info("OpenAI API 호출 완료")

    raw = response.choices[0].message.content

    if use_langfuse and langfuse:
        langfuse.flush()

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
