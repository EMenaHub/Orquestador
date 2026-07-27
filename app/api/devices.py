from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.core.auth import require_auth, UserInfo
from app.core import nautobot
from app.templates import templates

router = APIRouter(prefix="/api", tags=["devices"])


@router.get("/devices", response_class=HTMLResponse)
async def list_devices(
    request: Request,
    region: str,
    _user: UserInfo = Depends(require_auth),
):
    devices = await nautobot.get_devices(region)
    return templates.TemplateResponse(
        request, "partials/dispositivos.html", {"devices": devices}
    )
