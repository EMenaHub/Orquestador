from abc import ABC, abstractmethod
import os

import httpx

from app.config import settings


class OxidizedClient(ABC):
    @abstractmethod
    async def get_config(self, hostname: str) -> str | None: ...


class OxidizedAPIClient(OxidizedClient):
    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.token = token

    async def get_config(self, hostname: str) -> str | None:
        headers = {}
        if self.token:
            headers["Authorization"] = f"Token {self.token}"

        async with httpx.AsyncClient(
            base_url=self.base_url, headers=headers, timeout=30
        ) as client:
            resp = await client.get(f"/node/fetch/{hostname}")

        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.text


class OxidizedGitClient(OxidizedClient):
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    async def get_config(self, hostname: str) -> str | None:
        import asyncio

        filepath = os.path.join(self.repo_path, hostname)
        for ext in ("", ".cfg", ".conf"):
            path = filepath + ext
            if os.path.isfile(path):
                loop = asyncio.get_running_loop()
                with open(path, "r") as f:
                    return await loop.run_in_executor(None, f.read)
        return None


def create_oxidized_client() -> OxidizedClient:
    if settings.oxidized_mode == "git":
        path = settings.oxidized_git_repo_path
        if not path:
            raise ValueError("OXIDIZED_GIT_REPO_PATH is required when OXIDIZED_MODE=git")
        return OxidizedGitClient(path)

    return OxidizedAPIClient(
        base_url=settings.oxidized_api_url or "",
        token=settings.oxidized_api_token,
    )
