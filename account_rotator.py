import asyncio
import logging
import random
import time
from typing import Dict, List, Optional
from telethon import TelegramClient, errors

logger = logging.getLogger("AccountRotator")


class AccountSession:
    def __init__(self, session_name: str, api_id: int, api_hash: str, phone: Optional[str] = None):
        self.session_name = session_name
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.client: Optional[TelegramClient] = None
        self.cooldown_until: float = 0.0
        self.total_requests: int = 0
        self.is_connected: bool = False

    async def connect(self):
        if not self.client:
            self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        if not self.client.is_connected():
            await self.client.start(phone=self.phone)
            self.is_connected = True
            me = await self.client.get_me()
            logger.info(f"Session '{self.session_name}' connected as @{me.username or me.id}")

    async def disconnect(self):
        if self.client and self.client.is_connected():
            await self.client.disconnect()
            self.is_connected = False

    def is_available(self) -> bool:
        return time.time() >= self.cooldown_until

    def set_cooldown(self, seconds: int):
        self.cooldown_until = time.time() + seconds
        logger.warning(f"Session '{self.session_name}' placed in cooldown for {seconds}s (until {self.cooldown_until})")


class SessionPool:
    """
    Manages multiple MTProto user accounts to distribute crawling loads,
    respect Telegram limits, and rotate accounts when hitting FloodWait.
    """
    def __init__(self, accounts: List[Dict]):
        """
        accounts = [
            {"session_name": "session_1", "api_id": 12345, "api_hash": "xxx", "phone": "+1..."},
            {"session_name": "session_2", "api_id": 67890, "api_hash": "yyy", "phone": "+1..."},
        ]
        """
        self.sessions: List[AccountSession] = [
            AccountSession(
                acc["session_name"],
                acc["api_id"],
                acc["api_hash"],
                acc.get("phone"),
            )
            for acc in accounts
        ]
        self._current_index = 0

    async def init_all(self):
        for s in self.sessions:
            try:
                await s.connect()
            except Exception as e:
                logger.error(f"Failed to initialize session {s.session_name}: {e}")

    async def close_all(self):
        for s in self.sessions:
            await s.disconnect()

    def get_active_session(self) -> Optional[AccountSession]:
        """Returns the next available session in a round-robin rotation."""
        if not self.sessions:
            return None

        for _ in range(len(self.sessions)):
            sess = self.sessions[self._current_index]
            self._current_index = (self._current_index + 1) % len(self.sessions)
            if sess.is_available():
                return sess

        return None

    async def wait_for_available_session(self) -> AccountSession:
        """Waits until at least one session cools down if all are busy/rate-limited."""
        while True:
            sess = self.get_active_session()
            if sess:
                return sess
            
            # Find earliest available cooldown
            min_wait = min(s.cooldown_until - time.time() for s in self.sessions)
            sleep_time = max(5.0, min_wait + 1.0)
            logger.info(f"All sessions in cooldown. Waiting {sleep_time:.1f}s for next available session...")
            await asyncio.sleep(sleep_time)
