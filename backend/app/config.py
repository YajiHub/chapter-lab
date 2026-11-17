from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Repo-root .env when running from backend/, local .env otherwise; real env vars win.
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    database_url: str = "postgresql+psycopg://chapterlab:chapterlab@localhost:5432/chapterlab"
    app_version: str = "dev"
    render_git_commit: str | None = None
    public_origin: str = ""
    cookie_secure: bool = True
    session_hours: int = 12

    # Generation
    provider_mode: str = "chain"  # "chain" (real providers) or "stub" (tests/CI)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    openrouter_api_key: str = ""
    fallback_enabled: bool = True
    generations_per_hour: int = 5
    global_daily_generation_cap: int = 200
    max_notes_chars: int = 6000

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, v: str) -> str:
        # Neon/Render hand out postgresql:// URLs; SQLAlchemy needs the psycopg 3 driver name.
        for prefix in ("postgres://", "postgresql://"):
            if v.startswith(prefix):
                return "postgresql+psycopg://" + v[len(prefix) :]
        return v

    @property
    def version(self) -> str:
        return self.render_git_commit or self.app_version


@lru_cache
def get_settings() -> Settings:
    return Settings()
