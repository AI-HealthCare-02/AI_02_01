"""
챌린지 레포지토리 — DB 쿼리 모음

위치: backend/app/repositories/challenge_repository.py
역할: challenges, user_challenges, challenge_logs 테이블의 CRUD 쿼리
"""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.challenges import (
    Challenge,
    ChallengeLog,
    UserChallenge,
    UserChallengeStatusEnum,
    VerificationMethodEnum,
)


class ChallengeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ══════════════════════════════════════════
    # challenges (챌린지 풀)
    # ══════════════════════════════════════════

    async def get_all_challenges(self) -> list[Challenge]:
        """전체 챌린지 목록 조회"""
        result = await self.session.execute(select(Challenge))
        return list(result.scalars().all())

    async def get_challenge_by_id(self, challenge_id: int) -> Challenge | None:
        """챌린지 단건 조회 (존재 여부 확인용)"""
        result = await self.session.execute(select(Challenge).where(Challenge.id == challenge_id))
        return result.scalar_one_or_none()

    # ══════════════════════════════════════════
    # user_challenges (참여 관리)
    # ══════════════════════════════════════════

    async def get_user_challenge_by_id(self, user_challenge_id: int) -> UserChallenge | None:
        """사용자 챌린지 단건 조회"""
        result = await self.session.execute(select(UserChallenge).where(UserChallenge.id == user_challenge_id))
        return result.scalar_one_or_none()

    async def get_active_user_challenge(self, user_id: int, challenge_id: int) -> UserChallenge | None:
        """해당 유저가 이 챌린지에 이미 active로 참여 중인지 확인 (중복 참여 방지)"""
        result = await self.session.execute(
            select(UserChallenge).where(
                UserChallenge.user_id == user_id,
                UserChallenge.challenge_id == challenge_id,
                UserChallenge.status == UserChallengeStatusEnum.ACTIVE,
            )
        )
        return result.scalar_one_or_none()

    async def create_user_challenge(self, user_id: int, challenge_id: int, start_date: date) -> UserChallenge:
        """챌린지 참여 등록 (user_challenges INSERT)"""
        user_challenge = UserChallenge(
            user_id=user_id,
            challenge_id=challenge_id,
            status=UserChallengeStatusEnum.ACTIVE,
            current_streak=0,
            start_date=start_date,
        )
        self.session.add(user_challenge)
        await self.session.commit()
        await self.session.refresh(user_challenge)
        return user_challenge

    async def update_status(self, user_challenge: UserChallenge, new_status: UserChallengeStatusEnum) -> UserChallenge:
        """챌린지 상태 변경 (active → abandoned / completed)"""
        user_challenge.status = new_status
        await self.session.commit()
        await self.session.refresh(user_challenge)
        return user_challenge

    async def update_streak(self, user_challenge: UserChallenge, new_streak: int) -> None:
        """연속 달성 일수 업데이트"""
        user_challenge.current_streak = new_streak
        await self.session.commit()

    # ══════════════════════════════════════════
    # challenge_logs (인증 기록)
    # ══════════════════════════════════════════

    async def get_log_by_date(self, user_challenge_id: int, log_date: date) -> ChallengeLog | None:
        """해당 날짜에 이미 인증했는지 확인 (하루 1회 제한)"""
        result = await self.session.execute(
            select(ChallengeLog).where(
                ChallengeLog.user_challenge_id == user_challenge_id,
                ChallengeLog.log_date == log_date,
            )
        )
        return result.scalar_one_or_none()

    async def create_log(
        self,
        user_challenge_id: int,
        log_date: date,
        verification_type: VerificationMethodEnum,
        input_value: str | None = None,
        cv_result_id: int | None = None,
    ) -> ChallengeLog:
        """인증 기록 생성 (challenge_logs INSERT)"""
        log = ChallengeLog(
            user_challenge_id=user_challenge_id,
            log_date=log_date,
            verification_type=verification_type,
            input_value=input_value,
            cv_result_id=cv_result_id,
        )
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def count_logs(self, user_challenge_id: int) -> int:
        """해당 챌린지의 총 인증 횟수 조회 (완료 판정용)"""
        result = await self.session.execute(
            select(func.count()).where(ChallengeLog.user_challenge_id == user_challenge_id)
        )
        return result.scalar() or 0

    async def get_active_challenge_ids(self, user_id: int) -> list[int]:
        """유저가 현재 참여 중인 챌린지 ID 목록"""
        result = await self.session.execute(
            select(UserChallenge.challenge_id).where(
                UserChallenge.user_id == user_id,
                UserChallenge.status == UserChallengeStatusEnum.ACTIVE,
            )
        )
        return list(result.scalars().all())

    async def get_completed_challenge_ids(self, user_id: int) -> list[int]:
        """유저가 완료한 챌린지 ID 목록"""
        result = await self.session.execute(
            select(UserChallenge.challenge_id).where(
                UserChallenge.user_id == user_id,
                UserChallenge.status == UserChallengeStatusEnum.COMPLETED,
            )
        )
        return list(result.scalars().all())

    async def get_my_active_challenges(self, user_id: int) -> list[tuple[UserChallenge, Challenge]]:
        """유저의 진행 중인 챌린지 목록 (UserChallenge + Challenge 조인)"""
        result = await self.session.execute(
            select(UserChallenge, Challenge)
            .join(Challenge, UserChallenge.challenge_id == Challenge.id)
            .where(
                UserChallenge.user_id == user_id,
                UserChallenge.status == UserChallengeStatusEnum.ACTIVE,
            )
            .order_by(UserChallenge.id.desc())
        )
        return list(result.all())
