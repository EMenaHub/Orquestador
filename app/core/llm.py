from collections.abc import AsyncGenerator

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

from app.config import settings
from app.core.prompts import prompt_template

MAX_CONFIG_CHARS = 8000
LLM_TIMEOUT = 60

_llm: ChatOpenAI | None = None


def _get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        if not settings.openwebui_api_key:
            raise ValueError(
                "OPENWEBUI_API_KEY no está configurada. "
                "Revisa el archivo .env."
            )
        if not settings.openwebui_base_url:
            raise ValueError(
                "OPENWEBUI_BASE_URL no está configurada. "
                "Revisa el archivo .env."
            )
        _llm = ChatOpenAI(
            model=settings.openwebui_model,
            api_key=settings.openwebui_api_key,
            base_url=settings.openwebui_base_url,
            temperature=0.1,
            max_tokens=2048,
            request_timeout=LLM_TIMEOUT,
        )
    return _llm


def _truncate_config(config: str, max_chars: int = MAX_CONFIG_CHARS) -> str:
    if len(config) <= max_chars:
        return config
    return config[:max_chars] + "\n\n## [CONFIGURACIÓN TRUNCADA]"


async def ask_stream(hostname: str, config: str, question: str) -> AsyncGenerator[str, None]:
    chain = prompt_template | _get_llm() | StrOutputParser()

    truncated = _truncate_config(config)
    async for chunk in chain.astream(
        {"hostname": hostname, "config": truncated, "question": question}
    ):
        yield chunk
