from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.core.auth import require_auth, UserInfo
from app.core import nautobot
from app.templates import templates

router = APIRouter(prefix="/api", tags=["tenants"])


@router.get("/tenants", response_class=HTMLResponse)
async def list_tenants(
    request: Request,
    _user: UserInfo = Depends(require_auth),
):
    tenants = await nautobot.get_tenants()
    devices_by_tenant = await nautobot.get_devices_by_tenant()
    return templates.TemplateResponse(
        request,
        "partials/tenants.html",
        {
            "tenants": tenants,
            "devices_by_tenant": devices_by_tenant,
            "nautobot_ok": nautobot.nautobot_available(),
        },
    )
