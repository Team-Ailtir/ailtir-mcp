from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ailtir_mcp_api_token: str = Field(..., min_length=1)
    log_format: str = Field(default="console")
    log_level: str = Field(default="INFO")
    api_mcp_url: str = Field(default="https://app.ailtir.ai/api-mcp")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()  # type: ignore[call-arg]
