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

    # Search Page Size
    SEARCH_PAGE_SIZE: int = 8

    # Web Server & Uptime Keep-Alive (for Render / Koyeb / Railway)
    PORT: int = int(os.getenv("PORT", 8080))
    PING_URL: Optional[str] = os.getenv("RENDER_EXTERNAL_URL", None)
    ENABLE_WEB_SERVER: bool = True

    # Admin user IDs allowed to trigger indexing via bot commands
    ADMIN_IDS: List[int] = []

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
