from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from urllib.parse import urlencode
import httpx

from app.core.auth import verify_google_token
from app.config import settings
from app.templates import templates

router = APIRouter(prefix="/auth", tags=["auth"])


def _redirect_uri(request: Request) -> str:
    return str(request.base_url.replace(path="/auth/callback"))


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@router.get("/google")
async def google_login(request: Request):
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": _redirect_uri(request),
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
    }
    return RedirectResponse(
        f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    )


@router.get("/callback")
async def auth_callback(request: Request, code: str):
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "redirect_uri": _redirect_uri(request),
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(token_url, data=data)
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Error exchanging auth code")

    id_token_str = resp.json()["id_token"]
    user = verify_google_token(id_token_str)
    if not user:
        raise HTTPException(status_code=403, detail="Dominio no permitido")

    response = RedirectResponse(url="/", status_code=302)
    request.session["user"] = {"email": user.email, "name": user.name}
    return response


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/auth/login", status_code=302)
