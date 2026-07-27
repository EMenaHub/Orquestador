from unittest.mock import patch
import pytest

from app.core import nautobot


@pytest.mark.asyncio
async def test_get_regions():
    nautobot._regions_cache.clear()
    fake_data = {"locations": [{"id": "1", "name": "Chile"}, {"id": "2", "name": "Brasil"}]}

    with patch("app.core.nautobot._graphql", return_value=fake_data):
        regions = await nautobot.get_regions()

    assert len(regions) == 2
    assert regions[0]["name"] == "Chile"


@pytest.mark.asyncio
async def test_get_devices():
    fake_data = {
        "devices": [{"id": "d1", "name": "EC-DC1-CORE-1"}, {"id": "d2", "name": "EC-DC1-CORE-2"}]
    }

    with patch("app.core.nautobot._graphql", return_value=fake_data):
        devices = await nautobot.get_devices("region-1")

    assert len(devices) == 2
    assert devices[0]["name"] == "EC-DC1-CORE-1"


@pytest.mark.asyncio
async def test_get_regions_cache():
    nautobot._regions_cache.clear()
    fake_data = {"locations": [{"id": "1", "name": "Chile"}]}

    with patch("app.core.nautobot._graphql", return_value=fake_data) as mock:
        await nautobot.get_regions()
        await nautobot.get_regions()

    assert mock.call_count == 1
