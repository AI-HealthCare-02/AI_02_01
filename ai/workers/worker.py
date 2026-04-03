"""
AI Worker 통합 모듈
ML1: XGBoost 위험도 예측
ML2: ChatGPT 건강 코멘트 생성
"""

import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from predicts import predicts, recalculate_risk
from prompts import SYSTEM_PROMPT, build_user_prompt

# 환경변수 로드
load_dotenv('/Users/admin/cardiovascular_ml/envs/local.env')
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ── ML1 함수 (XGBoost 예측)
def ml1_predict(user_data: dict) -> dict:
    """
    건강검진 수치 → 위험도 예측
    """
    return predicts(user_data)


# ── ML2 함수 (ChatGPT 코멘트)
def ml2_comment(user_info: dict) -> dict:
    """
    위험도 결과 → 건강 코멘트 생성
    """
    user_prompt = build_user_prompt(user_info)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0
    )

    raw = response.choices[0].message.content

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "evaluation": "건강 데이터를 분석했습니다.",
            "alert": None,
            "missions": [],
            "encouragement": "오늘도 건강한 하루 보내세요!"
        }


# ── ML1 + ML2 통합 함수
def predict_and_comment(user_data: dict,
                        nickname: str = '사용자',
                        challenge_days: int = 0) -> dict:
    """
    건강검진 수치 입력 → 위험도 예측 + 건강 코멘트 생성
    """
    # 1. ML1 예측
    ml1_result = ml1_predict(user_data)

    # 2. ML2 코멘트 생성
    user_info = {
        'nickname': nickname,
        'age': user_data['age'],
        'risk_percent': ml1_result['risk_percent'],
        'risk_grade': ml1_result['risk_grade'],
        'heart_age': ml1_result['heart_age'],
        'top_risk_factors': ml1_result['top_risk_factors'],
        'smoke': user_data['smoke'],
        'alco': user_data['alco'],
        'challenge_days': challenge_days
    }
    ml2_result = ml2_comment(user_info)

    return {
        "ml1": ml1_result,
        "ml2": ml2_result
    }


# ── 테스트
if __name__ == '__main__':
    sample = {
        'age': 45,
        'gender': 1,
        'height': 165,
        'weight': 70,
        'ap_hi': 140,
        'ap_lo': 90,
        'cholesterol': 2,
        'gluc': 1,
        'smoke': 1,
        'alco': 0,
        'active': 0
    }

    result = predict_and_comment(
        sample,
        nickname='건강이',
        challenge_days=3
    )

    print("=== ML1 결과 ===")
    for k, v in result['ml1'].items():
        print(f"{k}: {v}")

    print("\n=== ML2 결과 ===")
    for k, v in result['ml2'].items():
        print(f"{k}: {v}")