from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse

from app.core.auth import require_auth, UserInfo
from app.core.stream import start_query_stream, iter_stream
from app.templates import templates

router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query", response_class=HTMLResponse)
async def query_device(
    request: Request,
    hostname: str = Form(...),
    question: str = Form(...),
    _user: UserInfo = Depends(require_auth),
):
    try:
        stream_id = await start_query_stream(hostname, question)
    except ValueError as e:
        return templates.TemplateResponse(
            request,
            "partials/respuesta.html",
            {"error": str(e)},
        )

    return templates.TemplateResponse(
        request,
        "partials/sse.html",
        {"stream_id": stream_id},
    )


@router.get("/stream/{stream_id}")
async def stream_response(stream_id: str):
    return StreamingResponse(
        iter_stream(stream_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
