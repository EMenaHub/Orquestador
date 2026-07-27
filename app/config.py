from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    google_client_id: str
    google_client_secret: str
    allowed_domain: str = "@tuempresa.com"
    session_secret_key: str
    session_max_age: int = 43200

    nautobot_url: str
    nautobot_token: str

    oxidized_mode: str = "api"
    oxidized_api_url: str | None = None
    oxidized_api_token: str | None = None
    oxidized_git_repo_path: str | None = None

    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash-001"

    cache_ttl_regions: int = 600
    cache_ttl_devices: int = 300

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
