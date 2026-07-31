import logging
import sys

import structlog
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    log_format: str
    log_level: str
    api_mcp_url: str
    mcp_host: str
    mcp_port: int
    mcp_mount_path: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Values are loaded from the environment by pydantic-settings.
settings = Settings()  # type: ignore[call-arg]


def configure_logging() -> None:
    """Configure structlog and stdlib logging from settings."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(stream=sys.stderr, level=level, force=True)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
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
