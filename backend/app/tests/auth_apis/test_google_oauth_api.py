from starlette import status


async def test_google_authorize_returns_url(client):
    response = await client.get("/api/v1/auth/google/login", follow_redirects=False)
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    location = response.headers["location"]
    assert "accounts.google.com" in location
    assert "client_id" in location


async def test_google_login_missing_code(client):
    response = await client.post("/api/v1/auth/login/google", json={})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
