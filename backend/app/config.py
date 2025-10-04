from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    database_url: str = Field(default="postgresql+asyncpg://postgres:postgres@localhost:5432/ai_tutor", alias="DATABASE_URL")
    env: str = Field(default="development", alias="ENV")
    cors_origins: str = Field(default="*")
    tool_base_url: str = Field(default="http://localhost:8000", alias="TOOL_BASE_URL")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()  # type: ignore
