"""
Vision API 프롬프트 독립 테스트 스크립트
- Celery, Docker, Redis 없이 OpenAI API 직접 호출
- prompts.py에서 프롬프트를 가져와서 테스트
- 사용법: python test_vision.py
"""
import base64
import json
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from prompts import MEAL_FREE_PROMPT, MEAL_PAID_PROMPT, EXERCISE_PROMPT

# ──────────────────────────────────────────────
# 설정
# ──────────────────────────────────────────────
# .env 파일이나 환경변수에서 API 키 가져오기
# 없으면 아래에 직접 입력 (커밋 금지!)
API_KEY = os.getenv("OPENAI_API_KEY")

# 테스트할 이미지 경로
IMAGE_PATH = Path("test_images/딸기케이크.jpg")  # 테스트할 이미지 넣기

# 테스트할 프롬프트 선택: "free" / "paid" / "exercise"
TEST_MODE = "paid"

# ──────────────────────────────────────────────
# 프롬프트 매핑
# ──────────────────────────────────────────────
PROMPTS = {
    "free": MEAL_FREE_PROMPT,
    "paid": MEAL_PAID_PROMPT,
    "exercise": EXERCISE_PROMPT,
}

# 사용자 위험 요인 (테스트용, 없으면 빈 문자열)
USER_RISK_FACTORS = ""
# USER_RISK_FACTORS = "고혈압 위험군"
# USER_RISK_FACTORS = "고콜레스테롤 위험군"
# USER_RISK_FACTORS = "고혈당 위험군"


def main():
    # 이미지 파일 확인
    if not IMAGE_PATH.exists():
        print(f"이미지 파일이 없음: {IMAGE_PATH}")
        print(f"test_images/ 폴더에 테스트 이미지를 넣어주세요")
        return

    # 이미지 → base64
    with open(IMAGE_PATH, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode("utf-8")

    # 확장자로 media type 결정
    ext = IMAGE_PATH.suffix.lower()
    media_types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
    media_type = media_types.get(ext, "image/jpeg")

    # 프롬프트 선택
    prompt = PROMPTS.get(TEST_MODE, MEAL_FREE_PROMPT)
    print(f"테스트 모드: {TEST_MODE}")
    print(f"이미지: {IMAGE_PATH}")
    print("-" * 50)

    # 사용자 메시지 구성
    user_text = "이 식단을 분석해주세요. recommendations의 nutrient는 반드시 nutrition_ratio와 sodium_level 분석 결과에 따라 선택하세요."
    if TEST_MODE == "exercise":
        user_text = "이 운동 기록을 분석해주세요."
    if USER_RISK_FACTORS:
        user_text += f"\n사용자 위험 요인: {USER_RISK_FACTORS}"

    # OpenAI API 호출
    client = OpenAI(api_key=API_KEY)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{image_base64}"
                        },
                    },
                    {"type": "text", "text": user_text},
                ],
            },
        ],
    )

    # 결과 출력
    result = response.choices[0].message.content
    print("GPT 응답:")
    print("-" * 50)

    # JSON 파싱 시도
    try:
        parsed = json.loads(result)
        print(json.dumps(parsed, ensure_ascii=False, indent=2))
    except json.JSONDecodeError:
        print(result)
        print("\n⚠️ JSON 파싱 실패 - 프롬프트에서 JSON 강제 출력 규칙 확인 필요")

    # 토큰 사용량
    print("-" * 50)
    print(f"토큰 사용: {response.usage.total_tokens}")


if __name__ == "__main__":
    main()