from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.templates import templates
from app.api import auth, health, tenants, query

app = FastAPI(title="Orquestador", version="0.1.0")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret_key,
    max_age=settings.session_max_age,
    https_only=settings.session_https_only,
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(health.router)
app.include_router(tenants.router)
app.include_router(query.router)


@app.get("/")
async def index(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/auth/login", status_code=302)
    return templates.TemplateResponse(
        request, "index.html", {"user_email": user["email"]}
    )
