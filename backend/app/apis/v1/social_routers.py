from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import ORJSONResponse as Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.databases import get_db_session
from app.dependencies.security import get_request_user
from app.dtos.social import (
    CheerRequest,
    CheerResponse,
    FeedListResponse,
    FeedNotificationListResponse,
    FriendActionResponse,
    FriendListResponse,
    FriendRequestListResponse,
    FriendRequestSentResponse,
    UserSearchListResponse,
)
from app.models.users import User
from app.services.social import SocialService

# /api/v1/social 경로의 라우터. 사용자 검색 및 친구 관계 관리 API를 담당한다.
social_router = APIRouter(prefix="/social", tags=["social"])


@social_router.get(
    "/users/search",
    response_model=UserSearchListResponse,
    status_code=status.HTTP_200_OK,
    summary="사용자 닉네임 검색",
    description="닉네임 키워드로 사용자를 검색한다. 자신은 제외되며, 각 결과에 친구 여부(is_friend)가 포함된다. 최대 20건 반환.",
)
async def search_users(
    nickname: Annotated[str, Query(min_length=1, max_length=20, description="검색할 닉네임 키워드")],
    user: Annotated[User, Depends(get_request_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    service = SocialService(session)
    result = await service.search_users(nickname, user)
    return Response(result.model_dump(), status_code=status.HTTP_200_OK)


@social_router.post(
    "/friends/request/{receiver_id}",
    response_model=FriendRequestSentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="친구 요청 전송",
    description="특정 사용자에게 친구 요청을 전송한다. 자기 자신, 이미 친구, 진행 중인 요청, 차단 상태인 경우 오류를 반환한다. 이전에 거절된 요청은 재전송 가능하다.",
)
async def send_friend_request(
    receiver_id: int,
    user: Annotated[User, Depends(get_request_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    service = SocialService(session)
    result = await service.send_friend_request(receiver_id, user)
    return Response(result.model_dump(), status_code=status.HTTP_201_CREATED)


@social_router.get(
    "/friends/requests",
    response_model=FriendRequestListResponse,
    status_code=status.HTTP_200_OK,
    summary="받은 친구 요청 목록 조회",
    description="현재 로그인 사용자가 받은 대기 중(PENDING) 친구 요청 목록을 최신순으로 조회한다.",
)
async def get_friend_requests(
    user: Annotated[User, Depends(get_request_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    service = SocialService(session)
    result = await service.get_pending_requests(user)
    return Response(result.model_dump(), status_code=status.HTTP_200_OK)


@social_router.patch(
    "/friends/requests/{request_id}/accept",
    response_model=FriendActionResponse,
    status_code=status.HTTP_200_OK,
    summary="친구 요청 수락",
    description="받은 친구 요청을 수락한다. 수락 시 양방향으로 친구 목록에 추가된다.",
)
async def accept_friend_request(
    request_id: int,
    user: Annotated[User, Depends(get_request_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    service = SocialService(session)
    result = await service.accept_friend_request(request_id, user)
    return Response(result.model_dump(), status_code=status.HTTP_200_OK)


@social_router.patch(
    "/friends/requests/{request_id}/reject",
    response_model=FriendActionResponse,
    status_code=status.HTTP_200_OK,
    summary="친구 요청 거절",
    description="받은 친구 요청을 거절한다. 거절된 요청은 상대방이 재전송할 수 있다.",
)
async def reject_friend_request(
    request_id: int,
    user: Annotated[User, Depends(get_request_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    service = SocialService(session)
    result = await service.reject_friend_request(request_id, user)
    return Response(result.model_dump(), status_code=status.HTTP_200_OK)


@social_router.get(
    "/friends",
    response_model=FriendListResponse,
    status_code=status.HTTP_200_OK,
    summary="친구 목록 조회",
    description="현재 로그인 사용자의 친구 목록을 최신 추가 순으로 조회한다.",
)
async def get_friend_list(
    user: Annotated[User, Depends(get_request_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    service = SocialService(session)
    result = await service.get_friend_list(user)
    return Response(result.model_dump(), status_code=status.HTTP_200_OK)


@social_router.get(
    "/feed",
    response_model=FeedListResponse,
    status_code=status.HTTP_200_OK,
    summary="소셜 피드 조회",
    description="친구들의 최근 챌린지 인증 피드를 최신순으로 조회한다.",
)
async def get_feed(
    user: Annotated[User, Depends(get_request_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    service = SocialService(session)
    result = await service.get_feed(user)
    return Response(result.model_dump(), status_code=status.HTTP_200_OK)


@social_router.post(
    "/feed/cheer",
    response_model=CheerResponse,
    status_code=status.HTTP_200_OK,
    summary="응원하기",
    description="친구의 챌린지 인증에 응원을 보낸다.",
)
async def cheer(
    payload: CheerRequest,
    user: Annotated[User, Depends(get_request_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    service = SocialService(session)
    result = await service.cheer(payload, user)
    return Response(result.model_dump(), status_code=status.HTTP_200_OK)


@social_router.get(
    "/feed/notifications",
    response_model=FeedNotificationListResponse,
    status_code=status.HTTP_200_OK,
    summary="피드 응원 알림 목록 조회",
    description="현재 로그인 사용자가 받은 친구 피드 응원 알림을 최신순으로 조회한다.",
)
async def get_feed_notifications(
    user: Annotated[User, Depends(get_request_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    service = SocialService(session)
    result = await service.get_feed_notifications(user)
    return Response(result.model_dump(), status_code=status.HTTP_200_OK)


@social_router.delete(
    "/friends/{friend_id}",
    response_model=FriendActionResponse,
    status_code=status.HTTP_200_OK,
    summary="친구 삭제",
    description="친구 관계를 삭제한다. 양방향으로 제거되며, 이후 재요청이 가능하다.",
)
async def delete_friend(
    friend_id: int,
    user: Annotated[User, Depends(get_request_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    service = SocialService(session)
    result = await service.delete_friend(friend_id, user)
    return Response(result.model_dump(), status_code=status.HTTP_200_OK)
