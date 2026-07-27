from collections.abc import AsyncGenerator

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

from app.config import settings
from app.core.prompts import prompt_template

MAX_CONFIG_TOKENS = 30000

_llm: ChatGoogleGenerativeAI | None = None


def _get_llm() -> ChatGoogleGenerativeAI:
    global _llm
    if _llm is None:
        _llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            api_key=settings.gemini_api_key,
            temperature=0.1,
            max_output_tokens=4096,
        )
    return _llm


def _truncate_config(config: str, max_tokens: int = MAX_CONFIG_TOKENS) -> str:
    if len(config) <= max_tokens:
        return config
    return config[:max_tokens] + "\n\n## [CONFIGURACIÓN TRUNCADA]"


async def ask_stream(hostname: str, config: str, question: str) -> AsyncGenerator[str, None]:
    chain = prompt_template | _get_llm() | StrOutputParser()

    truncated = _truncate_config(config)
    async for chunk in chain.astream(
        {"hostname": hostname, "config": truncated, "question": question}
    ):
        yield chunk
