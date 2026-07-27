import os

os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("SESSION_SECRET_KEY", "test-secret-key")
os.environ.setdefault("NAUTOBOT_URL", "http://nautobot.test")
os.environ.setdefault("NAUTOBOT_TOKEN", "test-token")
os.environ.setdefault("GEMINI_API_KEY", "test-api-key")

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.fixture
def auth_client(client):
    """Client with a valid signed session cookie."""
    from itsdangerous import TimestampSigner
    from base64 import b64encode
    import json

    secret = os.environ["SESSION_SECRET_KEY"]
    signer = TimestampSigner(secret)
    session_data = b64encode(json.dumps(
        {"user": {"email": "test@tuempresa.com", "name": "Test User"}}
    ).encode("utf-8"))
    signed = signer.sign(session_data).decode("utf-8")

    client.cookies.set("session", signed)
    return client
