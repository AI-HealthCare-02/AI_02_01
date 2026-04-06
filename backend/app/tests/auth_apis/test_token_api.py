from starlette import status


async def test_token_refresh_missing_token(client):
    response = await client.get("/api/v1/auth/token/refresh")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Refresh token is missing."
