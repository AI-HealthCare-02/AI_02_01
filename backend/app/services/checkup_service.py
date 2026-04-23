"""
Health Checkup OCR Service (REQ-HLTH-OCR)
건강검진 결과지 사진 → 수치 추출 → 폼 자동 입력용 JSON 반환
"""

import logging

from pydantic import ValidationError

from app.schemas.checkup import CheckupResult
from app.services.checkup_prompts import CHECKUP_PROMPT
from app.services.vision_client import call_vision_api

logger = logging.getLogger(__name__)


class CheckupService:
    async def analyze(self, image_bytes: bytes, media_type: str) -> dict:
        logger.info("건강검진 OCR 분석 시작")

        response = await call_vision_api(
            image_bytes=image_bytes,
            media_type=media_type,
            system_prompt=CHECKUP_PROMPT,
            user_text="이 건강검진 결과지를 분석해주세요.",
            model="gpt-4o-mini",
            detail="high",
            temperature=0,
        )

        try:
            parsed = CheckupResult(**response["result"])
        except ValidationError as e:
            logger.error("건강검진 OCR Pydantic 검증 실패: %s", e)
            raise RuntimeError(f"OCR 결과 파싱 실패: {e}") from e

        parsed = self._sanitize(parsed)

        if not parsed.is_valid:
            logger.warning("건강검진 결과지 아님: %s", parsed.note)

        if parsed.confidence == "low":
            logger.warning("건강검진 OCR 신뢰도 낮음 — 수치 확인 필요")

        return {
            "result": parsed.model_dump(),
            "usage": response["usage"],
        }

    def _sanitize(self, r: CheckupResult) -> CheckupResult:
        issues = []

        if r.birth_year is not None and not (1900 <= r.birth_year <= 2015):
            issues.append(f"birth_year 범위 이상: {r.birth_year}")
            r = r.model_copy(update={"birth_year": None})

        if r.height is not None and r.height >= 250:
            issues.append(f"height 범위 이상: {r.height}")
            r = r.model_copy(update={"height": None})

        if r.weight is not None and (r.weight <= 20 or r.weight >= 300):
            issues.append(f"weight 범위 이상: {r.weight}")
            r = r.model_copy(update={"weight": None})

        if r.glucose is not None and r.glucose <= 10:
            issues.append(f"glucose 범위 이상: {r.glucose}")
            r = r.model_copy(update={"glucose": None})

        if r.total_cholesterol is not None and r.total_cholesterol <= 50:
            issues.append(f"total_cholesterol 범위 이상: {r.total_cholesterol}")
            r = r.model_copy(update={"total_cholesterol": None})

        if (
            r.systolic_bp is not None
            and r.diastolic_bp is not None
            and r.systolic_bp < r.diastolic_bp
        ):
            issues.append(f"혈압 역전: systolic={r.systolic_bp} < diastolic={r.diastolic_bp}")
            r = r.model_copy(update={"systolic_bp": None, "diastolic_bp": None})

        if issues:
            logger.warning("후처리 보정 항목: %s", issues)
            note = (r.note or "") + " [보정됨: " + ", ".join(issues) + "]"
            r = r.model_copy(update={"confidence": "low", "note": note.strip()})

        return r
