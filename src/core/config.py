import logging
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).parent.parent.parent


class LoggingConfig(BaseModel):
    level: Literal[
        "debug",
        "info",
        "warning",
        "error",
        "critical",
    ] = Field(default="info")
    format: str = Field(
        default=(
            "[%(asctime)s.%(msecs)03d] %(module)10s:%(lineno)-3d %(levelname)-7s - %(message)s"
        )
    )
    date_format: str = Field(default="%Y-%m-%d %H:%M:%S")

    @property
    def level_value(self) -> int:
        return logging.getLevelNamesMapping()[self.level.upper()]


class Settings(BaseSettings):
    logging: LoggingConfig = Field(...)
    debug: bool = False
    auth_service_url: str = Field(...)
    places_service_url: str = Field(...)
    devices_service_url: str = Field(...)
    collector_service_url: str = Field(default="placebrain-collector-service:50054")
    jwt_secret: str = Field(...)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"


settings = Settings()  # type: ignore[call-arg]
