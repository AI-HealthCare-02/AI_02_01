"""
Vision API Client
OpenAI 클라이언트 초기화 + 공통 Vision API 호출 함수
"""

import base64
import json
import logging
import os

from langfuse.openai import AsyncOpenAI

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        _client = AsyncOpenAI(api_key=api_key)
    return _client


ALLOWED_MEDIA_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
}


def encode_image_bytes(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def validate_media_type(media_type: str) -> str:
    if media_type not in ALLOWED_MEDIA_TYPES:
        raise ValueError(f"지원하지 않는 이미지 형식입니다: {media_type}. 지원 형식: {', '.join(ALLOWED_MEDIA_TYPES)}")
    return media_type


def _extract_json(raw: str) -> str:  # noqa: C901
    stripped = raw.strip()

    if stripped.startswith("{"):
        return stripped

    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        return stripped

    start = stripped.find("{")
    if start == -1:
        raise json.JSONDecodeError("JSON 객체를 찾을 수 없습니다", stripped, 0)

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


MAX_RETRIES = 2

_PRICING = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
}


def _calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = _PRICING.get(model, _PRICING["gpt-4o-mini"])
    input_cost = prompt_tokens / 1_000_000 * pricing["input"]
    output_cost = completion_tokens / 1_000_000 * pricing["output"]
    return round(input_cost + output_cost, 8)


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
            json_str = _extract_json(raw_content)
            result = json.loads(json_str)

            usage = response.usage
            estimated_cost = _calculate_cost(
                model=model,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
            )

            logger.info(
                "Vision API 호출 성공 (시도 %d/%d) | 모델: %s | 토큰: %d | 비용: $%.6f",
                attempt,
                MAX_RETRIES,
                model,
                usage.total_tokens,
                estimated_cost,
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
            logger.warning("JSON 파싱 실패 (시도 %d/%d): %s", attempt, MAX_RETRIES, e)
            continue

        except Exception as e:
            logger.error("Vision API 호출 에러: %s", e)
            raise RuntimeError(f"Vision API 호출 실패: {e}") from e

    raise RuntimeError(f"JSON 파싱 {MAX_RETRIES}회 실패. 마지막 에러: {last_error}")
