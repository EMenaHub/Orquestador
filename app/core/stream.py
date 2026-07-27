import asyncio
import uuid
from collections.abc import AsyncGenerator

from app.core.oxidized import create_oxidized_client
from app.core.llm import ask_stream

_active_streams: dict[str, asyncio.Queue] = {}


async def start_query_stream(hostname: str, question: str) -> str:
    client = create_oxidized_client()
    config = await client.get_config(hostname)
    if not config:
        raise ValueError(f"Configuración no encontrada para {hostname}")

    stream_id = str(uuid.uuid4())
    queue: asyncio.Queue = asyncio.Queue()
    _active_streams[stream_id] = queue

    asyncio.create_task(_run_llm(stream_id, hostname, config, question))
    return stream_id


async def _run_llm(stream_id: str, hostname: str, config: str, question: str):
    queue = _active_streams.get(stream_id)
    if not queue:
        return

    try:
        async for chunk in ask_stream(hostname, config, question):
            await queue.put(chunk)
    except Exception as e:
        await queue.put(f"\n\n[Error: {e}]")
    finally:
        await queue.put(None)


async def iter_stream(stream_id: str) -> AsyncGenerator[str, None]:
    queue = _active_streams.get(stream_id)
    if not queue:
        yield "event: error\ndata: Stream no encontrado\n\n"
        return

    while True:
        chunk = await queue.get()
        if chunk is None:
            break
        yield f"data: {chunk}\n\n"

    _active_streams.pop(stream_id, None)
