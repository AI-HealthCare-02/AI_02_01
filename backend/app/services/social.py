import logging
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core import config
from app.dtos.social import (
    CheerRequest,
    CheerResponse,
    FeedItemResponse,
    FeedListResponse,
    FeedNotificationListResponse,
    FeedNotificationResponse,
    FriendActionResponse,
    FriendListResponse,
    FriendRequestListResponse,
    FriendRequestResponse,
    FriendRequestSentResponse,
    FriendResponse,
    UserSearchListResponse,
    UserSearchResponse,
)
from app.models.friendships import FriendshipStatusEnum
from app.models.users import User
from app.repositories.social_repository import SocialRepository

logger = logging.getLogger(__name__)


class SocialService:
    """사용자 검색, 친구 요청, 친구 목록 관리 비즈니스 로직"""

    def __init__(self, session: AsyncSession):
        self.repo = SocialRepository(session)

    async def search_users(self, keyword: str, current_user: User) -> UserSearchListResponse:
        """닉네임 키워드로 사용자 검색 (is_friend 여부 포함)"""
        users = await self.repo.search_users_by_nickname(keyword, current_user.id)
        logger.info("사용자 검색 - keyword: %s, 결과 수: %d", keyword, len(users))

        result = []
        for user in users:
            is_friend = await self.repo.is_friend(current_user.id, user.id)
            is_requested = await self.repo.has_pending_request(current_user.id, user.id)
            result.append(
                UserSearchResponse(
                    id=user.id,
                    nickname=user.nickname,
                    profile_image=user.profile_image,
                    character_stage=user.character_stage,
                    is_friend=is_friend,
                    is_requested=is_requested,
                )
            )
        return UserSearchListResponse(users=result)

    async def send_friend_request(self, receiver_id: int, current_user: User) -> FriendRequestSentResponse:
        """친구 요청 전송"""
        # 자기 자신에게 요청 불가
        if receiver_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="자기 자신에게 친구 요청을 보낼 수 없습니다.",
            )

        # 이미 친구인지 확인
        if await self.repo.is_friend(current_user.id, receiver_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 친구 관계입니다.",
            )

        # 기존 Friendship 레코드 확인 (UniqueConstraint 대응)
        existing = await self.repo.get_friendship(current_user.id, receiver_id)
        if existing:
            if existing.status == FriendshipStatusEnum.PENDING:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="이미 친구 요청이 진행 중입니다.",
                )
            if existing.status == FriendshipStatusEnum.BLOCKED:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="친구 요청을 보낼 수 없는 상대입니다.",
                )
            if existing.status == FriendshipStatusEnum.REJECTED:
                # 거절된 요청은 재요청 허용 (PENDING으로 복구)
                await self.repo.update_friendship_status(existing, FriendshipStatusEnum.PENDING)
                logger.info("친구 요청 재전송 - requester: %d → receiver: %d", current_user.id, receiver_id)
                return FriendRequestSentResponse(request_id=existing.id, message="친구 요청을 전송했습니다.")

        friendship = await self.repo.create_friendship(current_user.id, receiver_id)
        logger.info("친구 요청 전송 - requester: %d → receiver: %d", current_user.id, receiver_id)
        return FriendRequestSentResponse(request_id=friendship.id, message="친구 요청을 전송했습니다.")

    async def get_pending_requests(self, current_user: User) -> FriendRequestListResponse:
        """받은 친구 요청 목록 조회 (PENDING 상태만)"""
        rows = await self.repo.get_pending_requests(current_user.id)
        logger.info("친구 요청 목록 조회 - user_id: %d, count: %d", current_user.id, len(rows))

        requests = [
            FriendRequestResponse(
                id=friendship.id,
                requester_id=requester.id,
                requester_nickname=requester.nickname,
                requester_profile_image=requester.profile_image,
                created_at=friendship.created_at,
            )
            for friendship, requester in rows
        ]
        return FriendRequestListResponse(requests=requests)

    async def _get_request_for_receiver(self, request_id: int, current_user: User):
        """친구 요청 조회 및 수신자 권한 검증 (수락/거절 공통 로직)"""
        friendship = await self.repo.get_friendship_by_id(request_id)
        if not friendship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 친구 요청을 찾을 수 없습니다.",
            )
        if friendship.receiver_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="본인에게 온 친구 요청만 처리할 수 있습니다.",
            )
        if friendship.status != FriendshipStatusEnum.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="처리 가능한 상태의 친구 요청이 아닙니다.",
            )
        return friendship

    async def accept_friend_request(self, request_id: int, current_user: User) -> FriendActionResponse:
        """친구 요청 수락 (FriendList 양방향 추가)"""
        friendship = await self._get_request_for_receiver(request_id, current_user)

        await self.repo.update_friendship_status(friendship, FriendshipStatusEnum.ACCEPTED)
        # 양방향 friend_list 추가 (A→B, B→A)
        await self.repo.create_friend_entry(friendship.requester_id, friendship.receiver_id)
        await self.repo.create_friend_entry(friendship.receiver_id, friendship.requester_id)

        logger.info("친구 요청 수락 - request_id: %d", request_id)
        return FriendActionResponse(message="친구 요청을 수락했습니다.")

    async def reject_friend_request(self, request_id: int, current_user: User) -> FriendActionResponse:
        """친구 요청 거절"""
        friendship = await self._get_request_for_receiver(request_id, current_user)

        await self.repo.update_friendship_status(friendship, FriendshipStatusEnum.REJECTED)
        logger.info("친구 요청 거절 - request_id: %d", request_id)
        return FriendActionResponse(message="친구 요청을 거절했습니다.")

    async def get_friend_list(self, current_user: User) -> FriendListResponse:
        """친구 목록 조회"""
        rows = await self.repo.get_friend_list(current_user.id)
        logger.info("친구 목록 조회 - user_id: %d, count: %d", current_user.id, len(rows))

        friends = [
            FriendResponse(
                friend_id=friend.id,
                nickname=friend.nickname,
                profile_image=friend.profile_image,
                character_stage=friend.character_stage,
                created_at=entry.created_at,
            )
            for entry, friend in rows
        ]
        return FriendListResponse(friends=friends)

    async def delete_friend(self, friend_id: int, current_user: User) -> FriendActionResponse:
        """친구 삭제 (양방향 FriendList 삭제 + Friendship 레코드 삭제로 재요청 허용)"""
        if not await self.repo.is_friend(current_user.id, friend_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="친구 관계가 아닙니다.",
            )

        await self.repo.delete_friend(current_user.id, friend_id)
        await self.repo.delete_friendship_by_users(current_user.id, friend_id)

        logger.info("친구 삭제 - user_id: %d, friend_id: %d", current_user.id, friend_id)
        return FriendActionResponse(message="친구를 삭제했습니다.")

    async def get_feed(self, current_user: User) -> FeedListResponse:
        """친구들의 진행 중 챌린지와 오늘 인증 여부 조회"""
        today = datetime.now(config.TIMEZONE).date()
        rows = await self.repo.get_friends_feed(current_user.id, today)
        items = [
            FeedItemResponse(
                challenge_id=challenge.id,
                user_challenge_id=user_challenge.id,
                challenge_log_id=log.id if log else None,
                user_id=user.id,
                nickname=user.nickname or "사용자",
                profile_image=user.profile_image,
                challenge_title=challenge.title,
                log_date=str(log.log_date) if log else None,
                current_streak=user_challenge.current_streak,
                created_at=str(log.created_at) if log else str(user_challenge.start_date),
                certified_today=log is not None,
            )
            for user_challenge, challenge, user, log in rows
        ]
        logger.info("피드 조회 - user_id: %d, count: %d", current_user.id, len(items))
        return FeedListResponse(items=items)

    async def cheer(self, payload: CheerRequest, current_user: User) -> CheerResponse:
        """친구의 하루를 응원하고 하루 1회 알림을 생성한다."""
        sender_id = current_user.id
        sender_nickname = current_user.nickname
        receiver_id = payload.target_user_id

        if receiver_id == sender_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="나 자신에게는 응원을 보낼 수 없습니다.",
            )

        if not await self.repo.is_friend(sender_id, receiver_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="친구에게만 응원을 보낼 수 있습니다.",
            )

        receiver = await self.repo.get_user_by_id(receiver_id)
        if not receiver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="응원을 받을 사용자를 찾을 수 없습니다.",
            )

        challenge_log_id = payload.challenge_log_id
        if challenge_log_id is not None:
            row = await self.repo.get_feed_log_detail(challenge_log_id)
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="응원할 챌린지 인증을 찾을 수 없습니다.",
                )

            log, _user_challenge, _challenge, log_owner = row
            if log_owner.id != receiver_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="응원 대상 사용자와 챌린지 인증 작성자가 일치하지 않습니다.",
                )
            challenge_log_id = log.id

        existing = await self.repo.get_daily_cheer_notification(
            receiver_id=receiver_id,
            sender_id=sender_id,
            target_date=datetime.now(config.TIMEZONE).date(),
        )
        if existing:
            return CheerResponse(message="오늘은 이미 이 친구에게 응원을 보냈어요.", notification_id=existing.id)

        message = f"{sender_nickname}님이 오늘의 응원을 보냈어요."
        notification = await self.repo.create_cheer_notification(
            receiver_id=receiver_id,
            sender_id=sender_id,
            challenge_log_id=challenge_log_id,
            message=message,
        )

        logger.info(
            "응원하기 - sender_id: %d, receiver_id: %d, challenge_log_id: %d",
            sender_id,
            receiver_id,
            challenge_log_id or 0,
        )
        return CheerResponse(message="오늘의 응원을 보냈습니다! 💚", notification_id=notification.id)

    async def get_feed_notifications(self, current_user: User) -> FeedNotificationListResponse:
        """내가 받은 피드 응원 알림 목록 조회"""
        rows = await self.repo.get_feed_notifications(current_user.id)
        notifications = [
            FeedNotificationResponse(
                id=notification.id,
                sender_id=sender.id,
                sender_nickname=sender.nickname,
                sender_profile_image=sender.profile_image,
                challenge_log_id=notification.challenge_log_id,
                challenge_title=challenge.title if challenge else None,
                message=notification.message,
                read_at=notification.read_at,
                created_at=notification.created_at,
            )
            for notification, sender, challenge in rows
        ]
        logger.info("피드 응원 알림 조회 - user_id: %d, count: %d", current_user.id, len(notifications))
        return FeedNotificationListResponse(notifications=notifications)
