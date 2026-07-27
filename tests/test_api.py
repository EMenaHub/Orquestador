from unittest.mock import patch
import pytest


@pytest.mark.asyncio
async def test_regions_requires_auth(client):
    response = await client.get("/api/regions")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_regions_returns_html(auth_client):
    fake_data = {"locations": [{"id": "1", "name": "Chile"}]}
    with patch("app.core.nautobot._graphql", return_value=fake_data):
        response = await auth_client.get("/api/regions")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Chile" in response.text


@pytest.mark.asyncio
async def test_devices_requires_auth(client):
    response = await client.get("/api/devices?region=1")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_devices_returns_html(auth_client):
    fake_data = {"devices": [{"id": "d1", "name": "EC-DC1-CORE-1"}]}
    with patch("app.core.nautobot._graphql", return_value=fake_data):
        response = await auth_client.get("/api/devices", params={"region": "1"})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "EC-DC1-CORE-1" in response.text
