import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.core.oxidized import OxidizedAPIClient, OxidizedGitClient


@pytest.mark.asyncio
async def test_api_client_returns_config():
    client = OxidizedAPIClient(base_url="http://oxidized.test", token="test")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "hostname EC-DC1-CORE-1\n!"

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
        config = await client.get_config("EC-DC1-CORE-1")

    assert config == "hostname EC-DC1-CORE-1\n!"


@pytest.mark.asyncio
async def test_api_client_returns_none_on_404():
    client = OxidizedAPIClient(base_url="http://oxidized.test")

    mock_response = MagicMock()
    mock_response.status_code = 404

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
        config = await client.get_config("UNKNOWN-DEVICE")

    assert config is None


@pytest.mark.asyncio
async def test_git_client_returns_config():
    from unittest.mock import mock_open

    client = OxidizedGitClient(repo_path="/fake/path")

    with patch("os.path.isfile", return_value=True), \
         patch("builtins.open", mock_open(read_data="hostname SW-1\n!")):
        config = await client.get_config("SW-1")

    assert config == "hostname SW-1\n!"


@pytest.mark.asyncio
async def test_git_client_returns_none_when_not_found():
    client = OxidizedGitClient(repo_path="/fake/path")

    with patch("os.path.isfile", return_value=False):
        config = await client.get_config("NONEXISTENT")

    assert config is None
