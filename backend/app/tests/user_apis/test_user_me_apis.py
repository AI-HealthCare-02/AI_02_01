from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.models.users import User
from app.services.jwt import JwtService


async def _create_user_and_get_token(session: AsyncSession) -> tuple[User, str]:
    user = User(
        provider="google",
        provider_id="google_test_123",
        nickname="테스터",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    token = JwtService().create_access_token(user)
    return user, str(token)


async def test_get_user_me_success(client, db_session):
    user, access_token = await _create_user_and_get_token(db_session)
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["nickname"] == "테스터"
    assert response.json()["id"] == user.id


async def test_update_user_me_success(client, db_session):
    _, access_token = await _create_user_and_get_token(db_session)
    update_data = {"nickname": "수정후"}
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.patch("/api/v1/users/me", json=update_data, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["nickname"] == "수정후"


async def test_get_user_me_unauthorized(client):
    response = await client.get("/api/v1/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
