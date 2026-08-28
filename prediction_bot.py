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
logger = logging.getLogger("VenomPredictionBot")

BOT_TOKEN = os.getenv("PREDICTION_BOT_TOKEN", "8712477067:AAEKbiPxgzYwsOVUx5wM6F5gboB9s32e5l8")
DB_URL = os.getenv("PREDICTION_DB_URL", "sqlite+aiosqlite:///./prediction_bot.db")

engine = create_async_engine(DB_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class BettingChannel(Base):
    __tablename__ = "betting_channels"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    channel_title: Mapped[str] = mapped_column(String(255), default="Channel")
    added_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    auto_post: Mapped[bool] = mapped_column(Boolean, default=True)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

from signals_generator import VenomEaglePredictor

# ---------------- Bot Handlers ----------------

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def cmd_start(message: Message):
    text = (
        "🦅 <b>Welcome to VENOM EAGLE PREDICTIONS BOT</b>\n\n"
        "Institutional football match intelligence, AI banker predictions, and verified booking codes.\n\n"
        "⚡ <b>Features:</b>\n"
        "• EaglePredict-style match intelligence & tactical breakdown\n"
        "• Multi-Odds Banker Slips (Over 2.5, BTTS, Home Win, Correct Scores)\n"
        "• Instant SportyBet, Bet9ja & 1xBet Booking Codes\n"
        "• Auto-Poster Bot for Telegram Betting Channels\n\n"
        "Tap below to generate a detailed live match intelligence report:"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🦅 Generate Eagle Banker Intelligence", callback_data="gen_banker")],
            [InlineKeyboardButton(text="📢 Add to Betting Channel (Auto-Post)", callback_data="add_channel")],
        ]
    )
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data == "gen_banker")
async def cb_gen_banker(callback: CallbackQuery):
    slip = VenomEaglePredictor.generate_eagle_style_prediction()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔄 Analyze Another Match", callback_data="gen_banker")]]
    )
    await callback.message.answer(slip, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "add_channel")
async def cb_add_channel(callback: CallbackQuery):
    text = (
        "📢 <b>How to Auto-Post to your Betting Channel:</b>\n\n"
        "1. Open your Telegram Channel settings ➡️ <b>Administrators</b>.\n"
        "2. Add this bot as an Admin with <b>Post Messages</b> permission.\n"
        "3. Send <code>/link_channel</code> inside your channel.\n"
        "4. The bot will automatically drop daily match slips and booking codes to your subscribers!"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="« Back", callback_data="home")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

async def main():
    await init_db()
    logger.info("Venom Football Prediction Bot started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
