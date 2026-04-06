"""
Exercise Capture Service (REQ-CHAL-009)
운동 앱 스크린샷 OCR → 운동 데이터 추출 + 챌린지 인증

사용법:
    service = ExerciseService()
    result = await service.analyze(image_bytes, "image/png")
"""

import logging

from .client import call_vision_api
from .prompts import EXERCISE_PROMPT

logger = logging.getLogger(__name__)


class ExerciseService:
    """운동 캡처 인증 서비스"""

    async def analyze(
        self,
        image_bytes: bytes,
        media_type: str,
    ) -> dict:
        """
        운동 앱 스크린샷 분석
        - 모델: gpt-4o-mini | detail: high
        - 비용: ~$0.0022/장
        - 결과: 앱명, 운동 종류, 걸음수/거리/시간/칼로리, 인증 여부

        Args:
            image_bytes: 업로드된 스크린샷 바이너리
            media_type: MIME 타입

        Returns:
            dict: {"result": ExerciseResult, "usage": UsageInfo}
        """
        logger.info("운동 캡처 분석 시작")

        response = await call_vision_api(
            image_bytes=image_bytes,
            media_type=media_type,
            system_prompt=EXERCISE_PROMPT,
            user_text="이 운동 앱 스크린샷을 분석해주세요.",
            model="gpt-4o-mini",
            detail="high",
        )

        result = response["result"]

        # 인증 실패 로깅
        if not result.get("is_verified", False):
            logger.warning(
                f"운동 인증 실패: {result.get('note', '사유 없음')}"
            )

        # 신뢰도 낮음 로깅
        if result.get("confidence") == "low":
            logger.warning("운동 데이터 신뢰도 낮음 — 수치 확인 필요")

        return response
