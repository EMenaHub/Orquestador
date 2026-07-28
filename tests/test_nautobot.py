from unittest.mock import patch
import pytest

from app.core import nautobot
from app.config import settings


@pytest.mark.asyncio
async def test_get_tenants():
    nautobot._tenants_cache.clear()
    fake_data = {"tenants": [{"id": "t1", "name": "Zapping Chile"}, {"id": "t2", "name": "Zapping Brasil"}]}

    with patch("app.core.nautobot._graphql", return_value=fake_data):
        tenants = await nautobot.get_tenants()

    assert len(tenants) == 2
    assert tenants[0]["name"] == "Zapping Chile"


@pytest.mark.asyncio
async def test_get_tenants_cache():
    nautobot._tenants_cache.clear()
    fake_data = {"tenants": [{"id": "t1", "name": "Zapping Chile"}]}

    with patch("app.core.nautobot._graphql", return_value=fake_data) as mock:
        await nautobot.get_tenants()
        await nautobot.get_tenants()

    assert mock.call_count == 1


@pytest.mark.asyncio
async def test_get_devices_by_tenant():
    nautobot._devices_cache.clear()
    fake_data = {
        "devices": [
            {
                "id": "d1",
                "name": "EC-DC1-CORE-1",
                "role": {"name": "CORE"},
                "tenant": {"id": "t1", "name": "Zapping Chile"},
            },
            {
                "id": "d2",
                "name": "EC-DC1-AGG-1",
                "role": {"name": "AGG"},
                "tenant": {"id": "t1", "name": "Zapping Chile"},
            },
        ]
    }

    with (
        patch("app.core.nautobot._graphql", return_value=fake_data),
        patch("app.core.nautobot.MANUAL_DEVICES", []),
    ):
        groups = await nautobot.get_devices_by_tenant()

    assert len(groups) == 1
    assert groups[0]["name"] == "Zapping Chile"
    assert len(groups[0]["devices"]) == 2


@pytest.mark.asyncio
async def test_get_devices_by_tenant_filters_unknown_role():
    nautobot._devices_cache.clear()
    fake_data = {
        "devices": [
            {
                "id": "d1",
                "name": "EC-DC1-CORE-1",
                "role": {"name": "CORE"},
                "tenant": {"id": "t1", "name": "Zapping Chile"},
            },
            {
                "id": "d2",
                "name": "DECODER-1",
                "role": {"name": "DECODER"},
                "tenant": {"id": "t1", "name": "Zapping Chile"},
            },
        ]
    }

    saved = settings.nautobot_device_roles
    settings.nautobot_device_roles = "CORE"

    with (
        patch("app.core.nautobot._graphql", return_value=fake_data),
        patch("app.core.nautobot.MANUAL_DEVICES", []),
    ):
        groups = await nautobot.get_devices_by_tenant()

    settings.nautobot_device_roles = saved

    assert len(groups[0]["devices"]) == 1
    assert groups[0]["devices"][0]["name"] == "EC-DC1-CORE-1"


@pytest.mark.asyncio
async def test_get_devices_by_tenant_device_no_role():
    nautobot._devices_cache.clear()
    fake_data = {
        "devices": [
            {
                "id": "d1",
                "name": "NO-ROLE-DEVICE",
                "role": None,
                "tenant": {"id": "t1", "name": "Zapping Chile"},
            },
        ]
    }

    with (
        patch("app.core.nautobot._graphql", return_value=fake_data),
        patch("app.core.nautobot.MANUAL_DEVICES", []),
    ):
        groups = await nautobot.get_devices_by_tenant()

    assert len(groups) == 0
