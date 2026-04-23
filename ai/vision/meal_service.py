"""
Meal Analysis Service (REQ-HLTH-007)
식단 사진 분석: 무료(탄단지 비율) + 유료(상세 리포트, -300pt)

사용법:
    service = MealService()
    result = await service.analyze_free(image_bytes, "image/jpeg")
    result = await service.analyze_paid(image_bytes, "image/jpeg")
"""

import logging

from .client import call_vision_api
from .prompts import MEAL_FREE_PROMPT, MEAL_PAID_PROMPT
from .schemas import MealFreeResult, MealPaidResult

logger = logging.getLogger(__name__)


class MealService:
    """식단 사진 분석 서비스"""

    async def analyze_free(
        self,
        image_bytes: bytes,
        media_type: str,
        risk_factors: str = "",
    ) -> dict:
        """
        무료 식단 분석
        - 모델: gpt-4o-mini | detail: low
        - 비용: ~$0.0002/장
        - 결과: 음식명, 추정 칼로리, 탄단지 비율, 나트륨, 한 줄 피드백
        - 사용자 위험 요인이 있으면 맞춤 피드백 제공

        Args:
            image_bytes: 업로드된 이미지 바이너리
            media_type: MIME 타입 (image/jpeg 등)
            risk_factors: 사용자 심혈관 위험 요인 (예: "고혈압, 고콜레스테롤")

        Returns:
            dict: {"result": MealFreeResult, "usage": UsageInfo}
        """
        logger.info("식단 무료 분석 시작")

        user_text = "이 음식 사진을 분석해주세요."
        if risk_factors:
            user_text += f"\n\n사용자 위험 요인: {risk_factors}"

        response = await call_vision_api(
            image_bytes=image_bytes,
            media_type=media_type,
            system_prompt=MEAL_FREE_PROMPT,
            user_text=user_text,
            model="gpt-4o-mini",
            detail="low",
        )

        # Pydantic 검증: GPT 응답이 스키마에 맞는지 확인
        validated = MealFreeResult(**response["result"])
        response["result"] = validated.model_dump()

        # 음식 인식 불가 체크
        if validated.food_name == "인식 불가":
            logger.warning("음식 사진이 아닌 이미지가 업로드됨")

        return response

    async def analyze_paid(
        self,
        image_bytes: bytes,
        media_type: str,
        risk_factors: str = "",
    ) -> dict:
        """
        유료 상세 리포트 (-300pt)
        - 모델: gpt-4o-mini | detail: high
        - 비용: ~$0.0016/장
        - 결과: 상세 분석 + 영양소 추천 + 다음 식사 제안 + 점수
        - 추가: 추정 칼로리, 일일 권장 섭취량 대비 비율, 비타민/무기질 정보
        - 사용자 위험 요인이 있으면 맞춤 분석 제공

        Args:
            image_bytes: 업로드된 이미지 바이너리
            media_type: MIME 타입
            risk_factors: 사용자 심혈관 위험 요인 (예: "고혈압, 고콜레스테롤")

        Returns:
            dict: {"result": MealPaidResult, "usage": UsageInfo}

        Note:
            포인트 차감은 이 함수가 아닌 라우터(엔드포인트)에서 처리.
            서비스는 순수하게 분석만 담당.
        """
        logger.info("식단 유료 상세 분석 시작")

        user_text = "이 음식 사진을 상세 분석해주세요."
        if risk_factors:
            user_text += f"\n\n사용자 위험 요인: {risk_factors}"

        response = await call_vision_api(
            image_bytes=image_bytes,
            media_type=media_type,
            system_prompt=MEAL_PAID_PROMPT,
            user_text=user_text,
            model="gpt-4o-mini",
            detail="high",
        )

        # Pydantic 검증: GPT 응답이 스키마에 맞는지 확인
        validated = MealPaidResult(**response["result"])
        response["result"] = validated.model_dump()

        return response
