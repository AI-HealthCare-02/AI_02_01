from starlette import status


async def test_google_authorize_returns_url(client):
    response = await client.get("/api/v1/auth/google/authorize")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "authorization_url" in data
    assert "accounts.google.com" in data["authorization_url"]
    assert "client_id" in data["authorization_url"]


async def test_google_login_missing_code(client):
    response = await client.post("/api/v1/auth/google/login", json={})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
