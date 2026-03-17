from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    aws_region: str = Field(default="eu-west-1")
    log_format: str = Field(default="console")
    log_level: str = Field(default="INFO")
    mcp_api_url: str = Field(default="http://localhost:8001")
    s3_bucket: str = Field(default="kbs.ailtir.ai")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
