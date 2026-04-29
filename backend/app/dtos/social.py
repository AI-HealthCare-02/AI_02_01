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
