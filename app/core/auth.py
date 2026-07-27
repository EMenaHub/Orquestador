from fastapi import Request, HTTPException
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app.config import settings


class UserInfo:
    def __init__(self, email: str, name: str, picture: str | None = None):
        self.email = email
        self.name = name
        self.picture = picture

    @property
    def domain(self) -> str:
        return self.email.split("@")[1] if "@" in self.email else ""


def verify_google_token(token: str) -> UserInfo | None:
    try:
        info = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.google_client_id,
        )
    except ValueError:
        return None

    email = info.get("email", "")
    domain = email.split("@")[1] if "@" in email else ""

    if domain != settings.allowed_domain.lstrip("@"):
        return None

    return UserInfo(
        email=email,
        name=info.get("name", email),
        picture=info.get("picture"),
    )


def require_auth(request: Request) -> UserInfo:
    user_data = request.session.get("user")
    if not user_data:
        raise HTTPException(status_code=401, detail="No autenticado")
    return UserInfo(email=user_data["email"], name=user_data["name"])
