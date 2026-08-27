import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List

class Settings(BaseSettings):
    # Telegram MTProto Userbot API credentials (get from https://my.telegram.org)
    API_ID: int = 0
    API_HASH: str = ""
    PHONE_NUMBER: Optional[str] = None
    SESSION_NAME: str = "tg_indexer_session"
    TELEGRAM_STRING_SESSION: Optional[str] = None

    # Telegram Bot Token for Search Interface (from @BotFather)
    BOT_TOKEN: str = ""

    # Database URL: defaults to SQLite async, can be postgresql+asyncpg://user:pass@host:5432/dbname
    DATABASE_URL: str = "sqlite+aiosqlite:///./telegram_directory.db"

    # Scraping / Rate-limiting parameters
    REQUEST_DELAY_MIN: float = 3.0       # Minimum seconds between group/participant requests
    REQUEST_DELAY_MAX: float = 6.0       # Maximum seconds (jitter) to prevent predictable patterns
    BATCH_PAUSE_SECONDS: float = 30.0    # Pause after processing a batch of members
    MAX_MEMBERS_PER_GROUP: int = 5000    # Safety limit per group crawl
    SEARCH_PAGE_SIZE: int = 8            # Results per page in Telegram bot search UI

    # Admin user IDs allowed to trigger indexing via bot commands
    ADMIN_IDS: List[int] = []

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
