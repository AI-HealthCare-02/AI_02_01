from datetime import datetime

from pydantic import BaseModel

# ──────────────────────────────────────────────
# 사용자 검색
# ──────────────────────────────────────────────


class UserSearchResponse(BaseModel):
    """닉네임 검색 결과 사용자 단건"""

    id: int
    nickname: str
    profile_image: str | None
    character_stage: int
    is_friend: bool
    is_requested: bool


class UserSearchListResponse(BaseModel):
    """닉네임 검색 결과 목록"""

    users: list[UserSearchResponse]


# ──────────────────────────────────────────────
# 친구 요청
# ──────────────────────────────────────────────


class FriendRequestSentResponse(BaseModel):
    """친구 요청 전송 결과"""

    request_id: int
    message: str


class FriendRequestResponse(BaseModel):
    """받은 친구 요청 단건 (요청자 정보 포함)"""

    id: int
    requester_id: int
    requester_nickname: str
    requester_profile_image: str | None
    created_at: datetime


class FriendRequestListResponse(BaseModel):
    """받은 친구 요청 목록"""

    requests: list[FriendRequestResponse]


# ──────────────────────────────────────────────
# 친구 목록
# ──────────────────────────────────────────────


class FriendResponse(BaseModel):
    """친구 목록 단건"""

    friend_id: int
    nickname: str
    profile_image: str | None
    character_stage: int
    created_at: datetime


class FriendListResponse(BaseModel):
    """친구 목록"""

    friends: list[FriendResponse]


# ──────────────────────────────────────────────
# 공통 액션 응답
# ──────────────────────────────────────────────


class FriendActionResponse(BaseModel):
    """친구 요청 수락/거절/삭제 결과"""

    message: str


# ──────────────────────────────────────────────
# 소셜 피드
# ──────────────────────────────────────────────


class FeedItemResponse(BaseModel):
    """친구의 진행 중 챌린지 오늘 상태 단건"""

    challenge_id: int
    user_challenge_id: int
    challenge_log_id: int | None
    user_id: int
    nickname: str
    profile_image: str | None
    challenge_title: str
    log_date: str | None
    current_streak: int
    created_at: str
    certified_today: bool


class FeedListResponse(BaseModel):
    """소셜 피드 목록"""

    items: list[FeedItemResponse]


class CheerResponse(BaseModel):
    """응원하기 결과"""

    message: str
    notification_id: int | None = None


class CheerRequest(BaseModel):
    """응원하기 요청"""

    target_user_id: int
    challenge_log_id: int | None = None


class FeedNotificationResponse(BaseModel):
    """피드 응원 알림 단건"""

    id: int
    sender_id: int
    sender_nickname: str
    sender_profile_image: str | None
    challenge_log_id: int | None
    challenge_title: str | None
    message: str
    read_at: datetime | None
    created_at: datetime


class FeedNotificationListResponse(BaseModel):
    """피드 응원 알림 목록"""

    notifications: list[FeedNotificationResponse]
