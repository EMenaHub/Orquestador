from unittest.mock import patch
import pytest

from app.core import nautobot


@pytest.mark.asyncio
async def test_tenants_requires_auth(client):
    response = await client.get("/api/tenants")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_tenants_returns_html(auth_client):
    nautobot._tenants_cache.clear()
    nautobot._devices_cache.clear()

    fake_tenants = {"tenants": [{"id": "t1", "name": "Zapping Chile"}]}
    fake_devices = {
        "devices": [
            {
                "id": "d1",
                "name": "EC-DC1-CORE-1",
                "role": {"name": "CORE"},
                "tenant": {"id": "t1", "name": "Zapping Chile"},
            }
        ]
    }

    with patch("app.core.nautobot._graphql") as mock:
        mock.side_effect = [fake_tenants, fake_devices]
        response = await auth_client.get("/api/tenants")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Zapping Chile" in response.text
    assert "EC-DC1-CORE-1" in response.text


@pytest.mark.asyncio
async def test_tenants_shows_filtered_devices(auth_client):
    nautobot._tenants_cache.clear()
    nautobot._devices_cache.clear()

    fake_tenants = {"tenants": [{"id": "t1", "name": "Zapping Chile"}]}
    fake_devices = {
        "devices": [
            {
                "id": "d1",
                "name": "EC-DC1-CORE-1",
                "role": {"name": "CORE"},
                "tenant": {"id": "t1", "name": "Zapping Chile"},
            }
        ]
    }

    with patch("app.core.nautobot._graphql") as mock:
        mock.side_effect = [fake_tenants, fake_devices]
        response = await auth_client.get("/api/tenants")

    assert response.status_code == 200
    assert "EC-DC1-CORE-1" in response.text
