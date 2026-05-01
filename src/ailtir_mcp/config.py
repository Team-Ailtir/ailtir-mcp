import logging
import sys

import structlog
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


def configure_logging() -> None:
    """Configure structlog and stdlib logging from settings."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(stream=sys.stderr, level=level, force=True)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if settings.log_format == "json":
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[*shared_processors, structlog.processors.StackInfoRenderer(), renderer],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(sys.stderr),
        cache_logger_on_first_use=True,
    )
