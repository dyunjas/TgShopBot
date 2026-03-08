from pydantic_settings import BaseSettings
from pydantic import field_validator
from .logger_config import logger


class Settings(BaseSettings):
    DROP_BOT_TOKEN: str

    ORDERS_GROUP_ID: int
    ADMIN_IDS: list[int]
    OPERATOR_REWARD_RUB: int = 50

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    JWT_SECRET: str
    S3_ENDPOINT_URL: str | None = None
    S3_REGION: str | None = None
    S3_ACCESS_KEY_ID: str | None = None
    S3_SECRET_ACCESS_KEY: str | None = None
    S3_BUCKET_NAME: str | None = None
    S3_PUBLIC_BASE_URL: str | None = None
    S3_MEDIA_PREFIX: str = "m"
    S3_USE_PATH_STYLE: bool = False

    @field_validator("ADMIN_IDS", mode="before")
    def split_admin_ids(cls, v):
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def POSTGRES_ASYNC_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


try:
    settings = Settings()
    logger.info("Settings successfully loaded from .env")
except Exception as e:
    logger.exception(f"Error loadding settings from .env: {e}")
    raise
