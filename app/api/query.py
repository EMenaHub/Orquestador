from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse, StreamingResponse

from app.core.auth import require_auth, UserInfo
from app.core.oxidized import create_oxidized_client
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
    except Exception as e:
        return templates.TemplateResponse(
            request,
            "partials/respuesta.html",
            {"error": f"Error al conectar con Oxidized o LLM: {e}"},
        )

    return templates.TemplateResponse(
        request,
        "partials/sse.html",
        {"stream_id": stream_id},
    )


@router.get("/config/{hostname}")
async def fetch_config(
    hostname: str,
    _user: UserInfo = Depends(require_auth),
):
    client = create_oxidized_client()
    config = await client.get_config(hostname)
    if not config:
        raise HTTPException(status_code=404, detail=f"Config no encontrada para {hostname}")
    return PlainTextResponse(config)


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
