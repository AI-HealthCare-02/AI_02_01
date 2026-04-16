"""
챌린지 서비스 — 비즈니스 로직

위치: backend/app/services/challenge_service.py
역할: 검증(중복 참여, 하루 1회, 상태 확인) + 레포지토리 호출

패턴: auth.py 서비스 패턴 준수
  - __init__(self, session) → 레포지토리 주입
  - HTTPException으로 에러 반환
"""

import logging
from datetime import date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.models.challenges import (
    UserChallenge,
    UserChallengeStatusEnum,
    VerificationMethodEnum,
)
from app.repositories.challenge_repository import ChallengeRepository

logger = logging.getLogger(__name__)


class ChallengeService:
    def __init__(self, session: AsyncSession):
        self.repo = ChallengeRepository(session)

    # ══════════════════════════════════════════
    # 1. 챌린지 목록 조회
    # ══════════════════════════════════════════

    async def get_all_challenges(self):
        """전체 챌린지 풀 조회"""
        logger.info("전체 챌린지 목록 조회")
        return await self.repo.get_all_challenges()

    # ══════════════════════════════════════════
    # 2. 챌린지 선택 (참여)
    # ══════════════════════════════════════════

    async def join_challenge(self, user_id: int, challenge_id: int) -> UserChallenge:
        """
        챌린지 참여 등록
        검증:
          - 챌린지 존재 여부 (404)
          - 중복 참여 방지: 같은 챌린지에 active 상태가 이미 있으면 차단 (409)
        """
        logger.info("챌린지 참여 요청 - user_id: %d, challenge_id: %d", user_id, challenge_id)

        # 챌린지 존재 여부 확인
        challenge = await self.repo.get_challenge_by_id(challenge_id)
        if not challenge:
            logger.warning("존재하지 않는 챌린지 - challenge_id: %d", challenge_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"챌린지를 찾을 수 없습니다. (id: {challenge_id})",
            )

        # 중복 참여 방지
        existing = await self.repo.get_active_user_challenge(user_id, challenge_id)
        if existing:
            logger.warning(
                "이미 참여 중인 챌린지 - user_id: %d, challenge_id: %d",
                user_id, challenge_id,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 참여 중인 챌린지입니다.",
            )

        user_challenge = await self.repo.create_user_challenge(
            user_id=user_id,
            challenge_id=challenge_id,
            start_date=date.today(),
        )
        logger.info(
            "챌린지 참여 완료 - user_challenge_id: %d", user_challenge.id
        )
        return user_challenge

    # ══════════════════════════════════════════
    # 3. 챌린지 포기
    # ══════════════════════════════════════════

    async def abandon_challenge(
        self, user_challenge_id: int, user_id: int
    ) -> UserChallenge:
        """
        챌린지 포기 처리
        검증:
          - user_challenge 존재 여부 (404)
          - 소유권 (403) — 본인 챌린지만 포기 가능
          - active 상태만 포기 가능 (400)
        """
        logger.info(
            "챌린지 포기 요청 - user_challenge_id: %d, user_id: %d",
            user_challenge_id, user_id,
        )

        user_challenge = await self._get_active_user_challenge(
            user_challenge_id, user_id
        )

        updated = await self.repo.update_status(
            user_challenge, UserChallengeStatusEnum.ABANDONED
        )
        logger.info("챌린지 포기 완료 - user_challenge_id: %d", user_challenge_id)
        return updated

    # ══════════════════════════════════════════
    # 4. 챌린지 인증
    # ══════════════════════════════════════════

    async def log_daily(
        self,
        user_challenge_id: int,
        user_id: int,
        verification_type: VerificationMethodEnum,
        input_value: str | None = None,
        cv_result_id: int | None = None,
    ):
        """
        챌린지 인증 기록
        검증:
          - user_challenge 존재 여부 (404)
          - 소유권 (403) — 본인 챌린지만 인증 가능
          - active 상태만 인증 가능 (400)
          - 하루 1회 인증 제한 (409)
        처리:
          - challenge_logs에 기록 생성
          - current_streak 업데이트
          - 챌린지 기간 종료 시(마지막 날 포함) 최종 판정
        """
        logger.info(
            "챌린지 인증 요청 - user_challenge_id: %d, user_id: %d",
            user_challenge_id, user_id,
        )

        user_challenge = await self._get_active_user_challenge(
            user_challenge_id, user_id
        )

        # 하루 1회 인증 제한
        today = date.today()
        existing_log = await self.repo.get_log_by_date(user_challenge_id, today)
        if existing_log:
            logger.warning(
                "오늘 이미 인증 완료 - user_challenge_id: %d", user_challenge_id
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="오늘은 이미 인증을 완료했습니다.",
            )

        # 인증 기록 생성
        log = await self.repo.create_log(
            user_challenge_id=user_challenge_id,
            log_date=today,
            verification_type=verification_type,
            input_value=input_value,
            cv_result_id=cv_result_id,
        )

        # streak 업데이트
        new_streak = user_challenge.current_streak + 1
        await self.repo.update_streak(user_challenge, new_streak)

        # 챌린지 기간 종료 시 최종 판정 (마지막 날 인증 후 판정 포함)
        challenge = await self.repo.get_challenge_by_id(user_challenge.challenge_id)
        if challenge:
            end_date = user_challenge.start_date + timedelta(days=challenge.duration_days - 1)
            today = date.today()

            if today >= end_date:
                total_logs = await self.repo.count_logs(user_challenge_id)

                if total_logs >= challenge.required_success_days:
                    user_challenge.completed_at = datetime.now()
                    await self.repo.update_status(
                        user_challenge, UserChallengeStatusEnum.COMPLETED
                    )
                    logger.info(
                        "챌린지 성공! - user_challenge_id: %d, total_logs: %d/%d",
                        user_challenge_id, total_logs, challenge.required_success_days,
                    )
                else:
                    await self.repo.update_status(
                        user_challenge, UserChallengeStatusEnum.FAILED
                    )
                    logger.info(
                        "챌린지 실패 - user_challenge_id: %d, total_logs: %d/%d",
                        user_challenge_id, total_logs, challenge.required_success_days,
                    )

        logger.info(
            "인증 완료 - user_challenge_id: %d, streak: %d",
            user_challenge_id, new_streak,
        )
        return log

    # ══════════════════════════════════════════
    # 공통 헬퍼
    # ══════════════════════════════════════════

    async def _get_active_user_challenge(
        self, user_challenge_id: int, user_id: int
    ) -> UserChallenge:
        """
        user_challenge 조회 + 소유권 검증 + active 상태 검증
        포기, 챌린지 인증에서 공통으로 사용

        검증 순서 (중요):
          1. 존재 여부 (404)
          2. 소유권 (403) — JWT로 인증된 user_id와 user_challenge.user_id 비교
          3. active 상태 (400)
        """
        user_challenge = await self.repo.get_user_challenge_by_id(user_challenge_id)

        if not user_challenge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"참여 중인 챌린지를 찾을 수 없습니다. (id: {user_challenge_id})",
            )

        # 소유권 검증: 본인 챌린지가 아니면 403
        if user_challenge.user_id != user_id:
            logger.warning(
                "소유권 검증 실패 - user_challenge_id: %d, owner_id: %d, requester_id: %d",
                user_challenge_id, user_challenge.user_id, user_id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="본인의 챌린지가 아닙니다.",
            )

        if user_challenge.status != UserChallengeStatusEnum.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"이미 {user_challenge.status.value} 상태인 챌린지입니다.",
            )

        return user_challenge