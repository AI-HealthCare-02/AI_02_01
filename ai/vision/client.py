"""
Vision API Client
OpenAI 클라이언트 초기화 + 공통 Vision API 호출 함수

노트북의 call_vision_api()를 async로 변환한 버전
FastAPI에서 바로 await 가능
"""

import os
import json
import base64
import logging
from langfuse.openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# OpenAI 클라이언트 (싱글턴)
# ──────────────────────────────────────────────
_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    """OpenAI 클라이언트 싱글턴 반환"""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        _client = AsyncOpenAI(api_key=api_key)
    return _client


# ──────────────────────────────────────────────
# 이미지 유틸리티
# ──────────────────────────────────────────────
ALLOWED_MEDIA_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
}


def encode_image_bytes(image_bytes: bytes) -> str:
    """이미지 바이트를 base64 문자열로 변환"""
    return base64.b64encode(image_bytes).decode("utf-8")


def validate_media_type(media_type: str) -> str:
    """미디어 타입 검증 후 반환"""
    if media_type not in ALLOWED_MEDIA_TYPES:
        raise ValueError(
            f"지원하지 않는 이미지 형식입니다: {media_type}. "
            f"지원 형식: {', '.join(ALLOWED_MEDIA_TYPES)}"
        )
    return media_type


# ──────────────────────────────────────────────
# JSON 추출 유틸리티
# ──────────────────────────────────────────────
def _extract_json(raw: str) -> str:
    """
    GPT 응답에서 JSON 문자열 추출

    GPT가 JSON 앞뒤에 텍스트를 붙이는 3가지 패턴 대응:
    1. 순수 JSON → 그대로 반환
    2. ```json ... ``` 코드블록 → 코드블록 내부 추출
    3. 텍스트 + {JSON} + 텍스트 → 중괄호 범위 추출
    """
    stripped = raw.strip()

    # 패턴 1: 이미 순수 JSON
    if stripped.startswith("{"):
        return stripped

    # 패턴 2: ```json ... ``` 코드블록
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        return stripped

    # 패턴 3: 중괄호 범위 추출 (텍스트 + JSON 혼합)
    start = stripped.find("{")
    if start == -1:
        raise json.JSONDecodeError("JSON 객체를 찾을 수 없습니다", stripped, 0)

    # 중괄호 깊이 추적으로 올바른 끝 위치 탐색
    depth = 0
    in_string = False
    escape_next = False
    end = -1

    for i in range(start, len(stripped)):
        char = stripped[i]

        if escape_next:
            escape_next = False
            continue

        if char == "\\":
            escape_next = True
            continue

        if char == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                end = i
                break

    if end == -1:
        raise json.JSONDecodeError("JSON 닫는 괄호를 찾을 수 없습니다", stripped, start)

    return stripped[start : end + 1]


# ──────────────────────────────────────────────
# Vision API 호출 (핵심 함수)
# ──────────────────────────────────────────────
MAX_RETRIES = 2  # JSON 파싱 실패 시 재시도 횟수


async def call_vision_api(
    image_bytes: bytes,
    media_type: str,
    system_prompt: str,
    user_text: str = "이 사진을 분석해주세요.",
    model: str = "gpt-4o-mini",
    detail: str = "low",
    max_tokens: int = 1000,
    temperature: float = 1.0,
) -> dict:
    """
    Vision API 호출 → JSON dict 반환

    Args:
        image_bytes: 이미지 바이너리 데이터
        media_type: MIME 타입 (image/jpeg, image/png 등)
        system_prompt: system prompt 문자열
        user_text: 사용자 메시지
        model: OpenAI 모델명
        detail: low(고정 85토큰) / high(타일 분할)
        max_tokens: 최대 응답 토큰

    Returns:
        dict: GPT 응답을 파싱한 JSON + 메타데이터
        {
            "result": { ... },       # GPT 분석 결과
            "usage": {
                "prompt_tokens": int,
                "completion_tokens": int,
                "total_tokens": int,
                "estimated_cost": float,
            }
        }

    Raises:
        ValueError: 이미지 형식 오류
        RuntimeError: API 호출 실패 또는 JSON 파싱 실패
    """
    validate_media_type(media_type)
    base64_image = encode_image_bytes(image_bytes)
    client = get_client()

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{base64_image}",
                                    "detail": detail,
                                },
                            },
                            {
                                "type": "text",
                                "text": user_text,
                            },
                        ],
                    },
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )

            raw_content = response.choices[0].message.content.strip()

            # JSON 추출 (3가지 패턴 대응)
            json_str = _extract_json(raw_content)
            result = json.loads(json_str)

            # 비용 계산
            usage = response.usage
            estimated_cost = _calculate_cost(
                model=model,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
            )

            logger.info(
                f"Vision API 호출 성공 (시도 {attempt}/{MAX_RETRIES}) | "
                f"모델: {model} | 토큰: {usage.total_tokens} | "
                f"비용: ${estimated_cost:.6f}"
            )

            return {
                "result": result,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                    "estimated_cost": estimated_cost,
                },
            }

        except json.JSONDecodeError as e:
            last_error = e
            logger.warning(
                f"JSON 파싱 실패 (시도 {attempt}/{MAX_RETRIES}): {e}"
            )
            continue

        except Exception as e:
            logger.error(f"Vision API 호출 에러: {e}")
            raise RuntimeError(f"Vision API 호출 실패: {e}") from e

    raise RuntimeError(
        f"JSON 파싱 {MAX_RETRIES}회 실패. 마지막 에러: {last_error}"
    )


# ──────────────────────────────────────────────
# 비용 계산
# ──────────────────────────────────────────────
# 2024.03 기준 가격 (변동 가능)
_PRICING = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
}


def _calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """토큰 사용량 기반 비용 계산 (USD)"""
    pricing = _PRICING.get(model, _PRICING["gpt-4o-mini"])
    input_cost = prompt_tokens / 1_000_000 * pricing["input"]
    output_cost = completion_tokens / 1_000_000 * pricing["output"]
    return round(input_cost + output_cost, 8)
