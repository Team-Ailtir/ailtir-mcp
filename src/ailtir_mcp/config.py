from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    log_format: str = Field(default="console")
    log_level: str = Field(default="INFO")
    mcp_api_url: str = Field(default="http://localhost:8001")
    root_path: str = Field(..., min_length=1)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()  # type: ignore[call-arg]
