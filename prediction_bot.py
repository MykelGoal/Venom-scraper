import asyncio
import datetime
import logging
import os
import random

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart, ChatMemberUpdatedFilter, ADMINISTRATOR
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery, ChatMemberUpdated
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("VenomPredictionBot")

from database import get_sanitized_db_url

BOT_TOKEN = os.getenv("PREDICTION_BOT_TOKEN", "8712477067:AAEKbiPxgzYwsOVUx5wM6F5gboB9s32e5l8")
DB_URL = get_sanitized_db_url(os.getenv("DATABASE_URL") or os.getenv("PREDICTION_DB_URL", "sqlite+aiosqlite:///./prediction_bot.db"))

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

from live_analytics_engine import LiveFootballEngine

# ---------------- Bot Handlers ----------------

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def cmd_start(message: Message):
    text = (
        "🦅 <b>Welcome to VENOM EAGLE PREDICTIONS</b>\n\n"
        "Official clean daily banker predictions & football intelligence matching the exact @eaglepredict format.\n\n"
        "⚡ <b>Select an option below:</b>"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚽️ Get Today's Predictions (Clean Slip)", callback_data="gen_banker")],
            [InlineKeyboardButton(text="📢 Auto-Post to My Betting Channel", callback_data="add_channel")],
        ]
    )
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data == "home")
async def cb_home(callback: CallbackQuery):
    text = (
        "🦅 <b>Welcome to VENOM EAGLE PREDICTIONS</b>\n\n"
        "Official clean daily banker predictions & football intelligence matching the exact @eaglepredict format.\n\n"
        "⚡ <b>Select an option below:</b>"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚽️ Get Today's Predictions (Clean Slip)", callback_data="gen_banker")],
            [InlineKeyboardButton(text="📢 Auto-Post to My Betting Channel", callback_data="add_channel")],
        ]
    )
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "gen_banker")
async def cb_gen_banker(callback: CallbackQuery):
    slip = await LiveFootballEngine.generate_eagle_clean_prediction()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Refresh Predictions", callback_data="gen_banker")],
        ]
    )
    await callback.message.answer(slip, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "add_channel")
async def cb_add_channel(callback: CallbackQuery):
    text = (
        "📢 <b>How to Enable Auto-Posting to Your Channel:</b>\n\n"
        "1. Open your Telegram Channel settings ➡️ <b>Administrators</b>.\n"
        "2. Add <b>@venomeaglebot</b> as an Administrator with <i>'Post Messages'</i> permission.\n"
        "3. Once added, forward any message from your channel here (or type <code>/link_channel</code> in your channel).\n"
        "4. The bot will automatically post clean daily slips to your subscribers every morning! 🚀"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="« Back", callback_data="home")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

# Auto-link when added as Admin
@dp.my_chat_member()
async def bot_added_to_channel(event: ChatMemberUpdated):
    if event.chat.type in ["channel", "supergroup"]:
        if event.new_chat_member.status in ["administrator", "creator"]:
            channel_id = event.chat.id
            channel_title = event.chat.title or "Betting Channel"
            user_id = event.from_user.id
            async with AsyncSessionLocal() as session:
                existing = await session.execute(select(BettingChannel).where(BettingChannel.channel_id == channel_id))
                obj = existing.scalar_one_or_none()
                if not obj:
                    obj = BettingChannel(channel_id=channel_id, channel_title=channel_title, added_by=user_id, auto_post=True)
                    session.add(obj)
                    await session.commit()
            logger.info(f"Connected betting channel: {channel_title} ({channel_id})")
            try:
                welcome_post = (
                    f"🦅 <b>Venom Eagle Auto-Poster Connected!</b>\n\n"
                    f"This channel is now connected to verified daily football predictions in the official EaglePredict format.\n\n"
                    f"Daily slips will be posted automatically! ⚽️"
                )
                await bot.send_message(chat_id=channel_id, text=welcome_post, parse_mode="HTML")
            except Exception as e:
                logger.warning(f"Failed to send welcome message: {e}")

# Link via forward or command
@dp.message(F.forward_from_chat)
async def handle_forward_link(message: Message):
    if message.forward_from_chat.type == "channel":
        ch_id = message.forward_from_chat.id
        ch_title = message.forward_from_chat.title or "Channel"
        async with AsyncSessionLocal() as session:
            existing = await session.execute(select(BettingChannel).where(BettingChannel.channel_id == ch_id))
            obj = existing.scalar_one_or_none()
            if not obj:
                obj = BettingChannel(channel_id=ch_id, channel_title=ch_title, added_by=message.from_user.id, auto_post=True)
                session.add(obj)
                await session.commit()
        await message.answer(f"✅ <b>Successfully connected:</b> {ch_title}\nAuto-posting is now active!", parse_mode="HTML")

# Background auto-poster loop (posts every 8 hours)
async def auto_prediction_broadcaster():
    while True:
        try:
            async with AsyncSessionLocal() as session:
                res = await session.execute(select(BettingChannel).where(BettingChannel.auto_post == True))
                channels = res.scalars().all()
                if channels:
                    slip = await LiveFootballEngine.generate_eagle_clean_prediction()
                    for ch in channels:
                        try:
                            await bot.send_message(chat_id=ch.channel_id, text=slip, parse_mode="HTML")
                            logger.info(f"Auto-posted predictions to {ch.channel_title} ({ch.channel_id})")
                        except Exception as e:
                            logger.warning(f"Could not post predictions to {ch.channel_id}: {e}")
        except Exception as e:
            logger.error(f"Error in prediction broadcaster: {e}")
        await asyncio.sleep(28800)  # Every 8 hours

async def main():
    await init_db()
    asyncio.create_task(auto_prediction_broadcaster())
    logger.info("Venom Football Prediction Bot started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
