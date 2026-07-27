from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.core.auth import require_auth, UserInfo
from app.core import nautobot
from app.templates import templates

router = APIRouter(prefix="/api", tags=["regions"])


@router.get("/regions", response_class=HTMLResponse)
async def list_regions(
    request: Request,
    _user: UserInfo = Depends(require_auth),
):
    regions = await nautobot.get_regions()
    return templates.TemplateResponse(
        request, "partials/regiones.html", {"regions": regions}
    )
