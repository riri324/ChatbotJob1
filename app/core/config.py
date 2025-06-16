from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    open_ai_key: str = Field(..., env="OPEN_AI_KEY")         # matches .env
    open_ai_org: str = Field(None, env="OPEN_AI_ORG")        # matches .env
    elevenlabs_key: str = Field(..., env="ELEVENLABS_KEY")   # matches .env
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )

settings = Settings()
