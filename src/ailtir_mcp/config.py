from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ailtir_mcp_api_token: str = Field(default="")
    log_format: str = Field(default="console")
    log_level: str = Field(default="INFO")
    api_mcp_url: str = Field(default="https://app.ailtir.ai/api-mcp")
    mcp_host: str = Field(default="0.0.0.0")  # noqa: S104
    mcp_port: int = Field(default=8000)
    mcp_mount_path: str = Field(default="/ailtir-mcp")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
