import pytest


@pytest.mark.asyncio
async def test_login_page(client):
    response = await client.get("/auth/login")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_index_redirects_when_unauthenticated(client):
    response = await client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/auth/login"
