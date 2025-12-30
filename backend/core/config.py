from pydantic_settings import BaseSettings
from pydantic import field_validator

from .logger_config import logger

class Settings(BaseSettings):
    BOT_TOKEN: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    LAVA_SHOP_ID: str
    LAVA_SECRET_KEY: str
    SECRET_KEY: str
    ADMIN_IDS: list[int]
    PALLY_API_TOKEN: str
    PALLY_SHOP_ID: str
    ORDERS_GROUP_ID: int
    REVIEWS_CHANNEL_ID: int

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
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def POSTGRES_SYNC_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

try:
    settings = Settings()
    logger.info("Settings successfully loaded from .env")
except Exception as e:
    logger.exception(f"Error loadding settings from .env: {e}")
    raise