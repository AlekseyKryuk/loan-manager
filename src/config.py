from enum import Enum
from typing import Annotated

from pydantic import (
    AmqpDsn,
    BaseModel,
    PostgresDsn,
    RedisDsn
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggingLevel(Enum):
    CRITICAL: int = 50
    ERROR: int = 40
    WARNING: int = 30
    INFO: int = 20
    DEBUG: int = 10


class LoggingSettings(BaseModel):
    level: int = LoggingLevel.WARNING.value
    format: str = "%(asctime)s %(name)s %(levelname)s: %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"


class AuthSettings(BaseModel):
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int = 15


class DatabaseSettings(BaseModel):
    url: Annotated[str, PostgresDsn]
    echo: bool = False
    echo_pool: bool = False
    max_overflow: int = 10
    pool_size: int = 50

    naming_convention: dict[str, str] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_N_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }


class CacheSettings(BaseModel):
    url: Annotated[str, RedisDsn]
    max_connections: int = 10


class AmqpSettings(BaseModel):
    url: Annotated[str, AmqpDsn]


class PaginationParams(BaseModel):
    offset: int = 0
    limit: int = 100


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=("prod.env", ".env"),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        env_ignore_empty=True,
    )

    logging: LoggingSettings = LoggingSettings()
    pagination: PaginationParams = PaginationParams()
    auth: AuthSettings
    db: DatabaseSettings
    cache: CacheSettings
    # amqp: AmqpSettings


settings = Settings()
