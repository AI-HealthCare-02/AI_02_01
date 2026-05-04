from sqlalchemy import and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.challenges import Challenge, ChallengeLog, UserChallenge
from app.models.friend_list import FriendList
from app.models.friendships import Friendship, FriendshipStatusEnum
from app.models.users import User


class SocialRepository:
    """
    친구 요청(Friendship) 및 친구 목록(FriendList) 테이블에 대한 DB CRUD를 담당하는 레포지토리 클래스.
    사용자 닉네임 검색도 이 레포지토리에서 처리한다.
    """

    def __init__(self, session: AsyncSession):
        # 외부에서 주입받은 DB 세션 (FastAPI의 Depends를 통해 전달됨)
        self._session = session

    async def search_users_by_nickname(self, keyword: str, exclude_user_id: int) -> list[User]:
        """
        닉네임 키워드로 사용자 검색 (부분 일치, 자신 제외, 탈퇴 계정 제외).
        최대 20건 반환.
        """
        result = await self._session.execute(
            select(User)
            .where(
                User.nickname.contains(keyword),
                User.id != exclude_user_id,
                User.is_deleted == False,  # noqa: E712
            )
            .limit(20)
        )
        return list(result.scalars().all())

    async def get_friendship(self, user_a: int, user_b: int) -> Friendship | None:
        """
        두 사용자 간의 친구 요청 레코드 조회 (방향 무관).
        없으면 None 반환.
        """
        result = await self._session.execute(
            select(Friendship).where(
                or_(
                    and_(Friendship.requester_id == user_a, Friendship.receiver_id == user_b),
                    and_(Friendship.requester_id == user_b, Friendship.receiver_id == user_a),
                )
            )
        )
        return result.scalar_one_or_none()

    async def create_friendship(self, requester_id: int, receiver_id: int) -> Friendship:
        """
        친구 요청 생성 (PENDING 상태).
        commit 후 refresh하여 DB에서 자동 생성된 값(id, created_at 등)을 반영한다.
        """
        friendship = Friendship(
            requester_id=requester_id,
            receiver_id=receiver_id,
            status=FriendshipStatusEnum.PENDING,
        )
        self._session.add(friendship)
        await self._session.commit()
        await self._session.refresh(friendship)
        return friendship

    async def get_friendship_by_id(self, request_id: int) -> Friendship | None:
        """
        친구 요청 ID(PK)로 단건 조회.
        없으면 None 반환.
        """
        result = await self._session.execute(select(Friendship).where(Friendship.id == request_id))
        return result.scalar_one_or_none()

    async def update_friendship_status(self, friendship: Friendship, new_status: FriendshipStatusEnum) -> None:
        """친구 요청 상태 변경 (PENDING → ACCEPTED / REJECTED 등)"""
        friendship.status = new_status
        await self._session.commit()
        await self._session.refresh(friendship)

    async def get_pending_requests(self, user_id: int) -> list[tuple[Friendship, User]]:
        """
        로그인 사용자가 받은 PENDING 상태 친구 요청 목록 조회.
        요청자(User) 정보를 JOIN하여 함께 반환.
        """
        result = await self._session.execute(
            select(Friendship, User)
            .join(User, Friendship.requester_id == User.id)
            .where(
                Friendship.receiver_id == user_id,
                Friendship.status == FriendshipStatusEnum.PENDING,
            )
            .order_by(Friendship.created_at.desc())
        )
        return list(result.all())

    async def has_pending_request(self, requester_id: int, receiver_id: int) -> bool:
        """내가 상대방에게 보낸 PENDING 상태 친구 요청 존재 여부 확인"""
        result = await self._session.execute(
            select(Friendship).where(
                Friendship.requester_id == requester_id,
                Friendship.receiver_id == receiver_id,
                Friendship.status == FriendshipStatusEnum.PENDING,
            )
        )
        return result.scalar_one_or_none() is not None

    async def is_friend(self, user_id: int, friend_id: int) -> bool:
        """friend_list에서 친구 여부 확인"""
        result = await self._session.execute(
            select(FriendList).where(
                FriendList.user_id == user_id,
                FriendList.friend_id == friend_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def create_friend_entry(self, user_id: int, friend_id: int) -> FriendList:
        """
        friend_list 단방향 엔트리 생성.
        수락 시 양방향으로 2회 호출해야 한다 (A→B, B→A).
        """
        entry = FriendList(user_id=user_id, friend_id=friend_id)
        self._session.add(entry)
        await self._session.commit()
        await self._session.refresh(entry)
        return entry

    async def get_friend_list(self, user_id: int) -> list[tuple[FriendList, User]]:
        """
        친구 목록 조회 (친구 User 정보 JOIN 포함).
        최신 친구 추가 순으로 정렬.
        """
        result = await self._session.execute(
            select(FriendList, User)
            .join(User, FriendList.friend_id == User.id)
            .where(FriendList.user_id == user_id)
            .order_by(FriendList.created_at.desc())
        )
        return list(result.all())

    async def delete_friend(self, user_id: int, friend_id: int) -> None:
        """
        친구 삭제 (양방향 FriendList 제거).
        A→B, B→A 양쪽 엔트리를 모두 삭제한다.
        """
        await self._session.execute(
            delete(FriendList).where(
                or_(
                    and_(FriendList.user_id == user_id, FriendList.friend_id == friend_id),
                    and_(FriendList.user_id == friend_id, FriendList.friend_id == user_id),
                )
            )
        )
        await self._session.commit()

    async def get_friends_feed(self, user_id: int, limit: int = 20) -> list:
        """친구들의 최근 챌린지 인증 피드 조회 (최신순)"""
        result = await self._session.execute(
            select(ChallengeLog, UserChallenge, Challenge, User)
            .join(UserChallenge, ChallengeLog.user_challenge_id == UserChallenge.id)
            .join(Challenge, UserChallenge.challenge_id == Challenge.id)
            .join(User, UserChallenge.user_id == User.id)
            .join(FriendList, and_(
                FriendList.user_id == user_id,
                FriendList.friend_id == UserChallenge.user_id,
            ))
            .order_by(ChallengeLog.created_at.desc())
            .limit(limit)
        )
        return list(result.all())

    async def delete_friendship_by_users(self, user_a: int, user_b: int) -> None:
        """
        두 사용자 간 Friendship 레코드 삭제 (방향 무관).
        친구 삭제 후 재요청이 가능하도록 UniqueConstraint 레코드를 제거한다.
        """
        await self._session.execute(
            delete(Friendship).where(
                or_(
                    and_(Friendship.requester_id == user_a, Friendship.receiver_id == user_b),
                    and_(Friendship.requester_id == user_b, Friendship.receiver_id == user_a),
                )
            )
        )
        await self._session.commit()
