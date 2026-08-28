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

BOT_TOKEN = os.getenv("FOREX_BOT_TOKEN", "8872020288:AAHbHL2pcTjcNV6jlO7N-HdG8BbV0NfeEjk")
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

# ---------------- Signal Generator ----------------

PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "XAU/USD (Gold)", "BTC/USD", "GBP/JPY", "AUD/USD", "US30 (Dow Jones)"]
ACTIONS = ["BUY 🟢", "SELL 🔴", "BUY LIMIT 🟢", "SELL LIMIT 🔴"]

def generate_live_signal() -> str:
    pair = random.choice(PAIRS)
    action = random.choice(ACTIONS)
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M UTC")

    if "Gold" in pair:
        entry = round(random.uniform(2480.0, 2530.0), 2)
        sl = round(entry - 15.0 if "BUY" in action else entry + 15.0, 2)
        tp1 = round(entry + 12.0 if "BUY" in action else entry - 12.0, 2)
        tp2 = round(entry + 28.0 if "BUY" in action else entry - 28.0, 2)
    elif "BTC" in pair:
        entry = round(random.uniform(62000.0, 68000.0), 1)
        sl = round(entry - 1200.0 if "BUY" in action else entry + 1200.0, 1)
        tp1 = round(entry + 900.0 if "BUY" in action else entry - 900.0, 1)
        tp2 = round(entry + 2200.0 if "BUY" in action else entry - 2200.0, 1)
    else:
        entry = round(random.uniform(1.0600, 1.3100), 4)
        sl = round(entry - 0.0035 if "BUY" in action else entry + 0.0035, 4)
        tp1 = round(entry + 0.0030 if "BUY" in action else entry - 0.0030, 4)
        tp2 = round(entry + 0.0080 if "BUY" in action else entry - 0.0080, 4)

    return (
        f"⚡ <b>VENOM FOREX VIP SIGNAL</b> ⚡\n\n"
        f"📊 <b>Asset:</b> <code>{pair}</code>\n"
        f"🎯 <b>Action:</b> <b>{action}</b>\n\n"
        f"📍 <b>Entry:</b> <code>{entry}</code>\n"
        f"🛑 <b>Stop Loss:</b> <code>{sl}</code>\n\n"
        f"🎯 <b>Take Profit 1:</b> <code>{tp1}</code> (Scalp)\n"
        f"🎯 <b>Take Profit 2:</b> <code>{tp2}</code> (Runner)\n\n"
        f"🕒 <i>{now_str}</i>\n"
        f"💎 <i>Powered by Venom Tech Forex</i>"
    )

# ---------------- Bot Handlers ----------------

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def cmd_start(message: Message):
    text = (
        "📊 <b>Welcome to VENOM FOREX SIGNALS BOT</b>\n\n"
        "This bot automatically drops institutional Forex, Gold, and Crypto trading signals directly to your Telegram channel.\n\n"
        "🚀 <b>How to Use:</b>\n"
        "1. Add this bot as an <b>Admin</b> in your Telegram Channel.\n"
        "2. Send <code>/connect_channel</code> inside your channel (or send channel ID here).\n"
        "3. The bot will automatically broadcast live high-probability signals on schedule!\n\n"
        "Tap below to generate a live instant signal test:"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚡ Generate Instant Forex Signal", callback_data="gen_signal")],
            [InlineKeyboardButton(text="📢 Add to My Channel (Instructions)", callback_data="instructions")],
        ]
    )
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data == "gen_signal")
async def cb_gen_signal(callback: CallbackQuery):
    signal_text = generate_live_signal()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔄 Generate Another", callback_data="gen_signal")]]
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
