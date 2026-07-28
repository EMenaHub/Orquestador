from unittest.mock import patch, AsyncMock
import pytest


@pytest.mark.asyncio
async def test_query_requires_auth(client):
    response = await client.post("/api/query", data={"hostname": "test", "question": "test"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_query_fast_fail_when_no_config(auth_client):
    with patch(
        "app.core.oxidized.OxidizedAPIClient.get_config",
        new_callable=AsyncMock,
        return_value=None,
    ):
        response = await auth_client.post(
            "/api/query",
            data={"hostname": "UNKNOWN", "question": "test"},
        )

    assert response.status_code == 200
    assert "Configuración no encontrada" in response.text


@pytest.mark.asyncio
async def test_query_returns_sse_partial(auth_client):
    with patch(
        "app.core.oxidized.OxidizedAPIClient.get_config",
        new_callable=AsyncMock,
        return_value="hostname TEST\n!",
    ):
        response = await auth_client.post(
            "/api/query",
            data={"hostname": "TEST", "question": "¿qué interfaces tengo?"},
        )

    assert response.status_code == 200
    assert "sse-connect" in response.text
    assert "/api/stream/" in response.text


@pytest.mark.asyncio
async def test_stream_endpoint_returns_event_stream(auth_client):
    response = await auth_client.get("/api/stream/nonexistent")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")


@pytest.mark.asyncio
async def test_fetch_config_requires_auth(client):
    response = await client.get("/api/config/TEST")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_fetch_config_returns_plain_text(auth_client):
    with patch(
        "app.core.oxidized.OxidizedAPIClient.get_config",
        new_callable=AsyncMock,
        return_value="hostname TEST\n!\ninterface GigabitEthernet0/0\n",
    ):
        response = await auth_client.get("/api/config/TEST")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "interface GigabitEthernet0/0" in response.text


@pytest.mark.asyncio
async def test_fetch_config_returns_404(auth_client):
    with patch(
        "app.core.oxidized.OxidizedAPIClient.get_config",
        new_callable=AsyncMock,
        return_value=None,
    ):
        response = await auth_client.get("/api/config/UNKNOWN")

    assert response.status_code == 404
    assert "no encontrada" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_stream_with_valid_id():
    from app.core.stream import start_query_stream, _active_streams
    from app.core.oxidized import OxidizedAPIClient

    async def fake_stream(*args, **kwargs):
        for text in ["respuesta ", "del ", "LLM"]:
            yield text

    with patch.object(
        OxidizedAPIClient, "get_config",
        new_callable=AsyncMock,
        return_value="hostname TEST\n!",
    ), patch(
        "app.core.llm.ask_stream",
        side_effect=fake_stream,
    ):
        stream_id = await start_query_stream("TEST", "test question")
        assert stream_id in _active_streams

    _active_streams.clear()
