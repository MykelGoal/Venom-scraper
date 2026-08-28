import asyncio
import datetime
import logging
import os
import random

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("VenomForexBot")

BOT_TOKEN = os.getenv("FOREX_BOT_TOKEN", "8967863227:AAFVno4s0e3WkD5XGGNBJakGNU3O4kLOBEI")
DB_URL = os.getenv("FOREX_DB_URL", "sqlite+aiosqlite:///./forex_bot.db")

engine = create_async_engine(DB_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class ConnectedChannel(Base):
    __tablename__ = "connected_channels"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    channel_title: Mapped[str] = mapped_column(String(255), default="Channel")
    added_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    auto_post: Mapped[bool] = mapped_column(Boolean, default=True)
    interval_hours: Mapped[int] = mapped_column(Integer, default=4)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

from signals_generator import VenomForexAnalyzer

# ---------------- Bot Handlers ----------------

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def cmd_start(message: Message):
    text = (
        "⚡ <b>Welcome to VENOM INSTITUTIONAL FOREX BOT</b>\n\n"
        "Institutional Smart Money (SMC) Forex, Gold, and Crypto trading signals with real technical analysis rationale.\n\n"
        "🚀 <b>How to Use:</b>\n"
        "1. Add this bot as an <b>Admin</b> in your Telegram VIP Trading Channel.\n"
        "2. The bot will automatically broadcast live high-probability signals on schedule!\n\n"
        "Tap below to generate a live institutional signal breakdown:"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚡ Generate Institutional Signal", callback_data="gen_signal")],
            [InlineKeyboardButton(text="📢 Add to My Channel (Instructions)", callback_data="instructions")],
        ]
    )
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data == "gen_signal")
async def cb_gen_signal(callback: CallbackQuery):
    signal_text = VenomForexAnalyzer.generate_institutional_signal()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔄 Analyze Next Asset", callback_data="gen_signal")]]
    )
    await callback.message.answer(signal_text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "instructions")
async def cb_instructions(callback: CallbackQuery):
    text = (
        "📢 <b>How to Connect to your Channel:</b>\n\n"
        "1. Open your Telegram Channel settings ➡️ <b>Administrators</b>.\n"
        "2. Tap <b>Add Admin</b> and search for this bot username.\n"
        "3. Grant permission to <b>Post Messages</b>.\n"
        "4. Forward any message from your channel to this bot, and it will link automatically!"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="« Back", callback_data="home")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

# ---------------- Background Auto-Poster ----------------

async def auto_signal_broadcaster():
    """Broadcasts signals to all connected channels every 4 hours automatically."""
    while True:
        try:
            async with AsyncSessionLocal() as session:
                res = await session.execute(select(ConnectedChannel).where(ConnectedChannel.auto_post == True))
                channels = res.scalars().all()
                if channels:
                    signal = generate_live_signal()
                    for ch in channels:
                        try:
                            await bot.send_message(chat_id=ch.channel_id, text=signal, parse_mode="HTML")
                            logger.info(f"Broadcasted signal to channel {ch.channel_title} ({ch.channel_id})")
                        except Exception as e:
                            logger.warning(f"Could not post to {ch.channel_id}: {e}")
        except Exception as e:
            logger.error(f"Error in signal broadcaster: {e}")
        await asyncio.sleep(14400)  # Every 4 hours

async def main():
    await init_db()
    asyncio.create_task(auto_signal_broadcaster())
    logger.info("Venom Forex Bot started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
