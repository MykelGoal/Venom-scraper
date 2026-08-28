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
logger = logging.getLogger("VenomForexBot")

from database import get_sanitized_db_url

BOT_TOKEN = os.getenv("FOREX_BOT_TOKEN", "8967863227:AAFVno4s0e3WkD5XGGNBJakGNU3O4kLOBEI")
DB_URL = get_sanitized_db_url(os.getenv("DATABASE_URL") or os.getenv("FOREX_DB_URL", "sqlite+aiosqlite:///./forex_bot.db"))

engine = create_async_engine(DB_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class ConnectedChannel(Base):
    __tablename__ = "connected_channels"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    channel_title: Mapped[str] = mapped_column(String(255), default="Trading Channel")
    added_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    auto_post: Mapped[bool] = mapped_column(Boolean, default=True)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

from live_analytics_engine import LiveMarketEngine

# ---------------- Bot Handlers ----------------

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def cmd_start(message: Message):
    text = (
        "⚡ <b>Welcome to VENOM LIVE FOREX VIP BOT</b>\n\n"
        "Real-time live Smart Money Concepts (SMC) signals for Forex, Gold (XAU/USD), and Crypto backed by live market feeds.\n\n"
        "🚀 <b>Features:</b>\n"
        "• 100% Live Market Prices (ECB / CoinGecko Live Feed)\n"
        "• High-Probability Setups: Entry, SL, TP1, TP2, TP3\n"
        "• SMC Technical Rationale & Liquidity Sweep Analysis\n"
        "• Automated Signal Broadcasting for Telegram Channels\n\n"
        "Tap below to get an instant institutional signal:"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚡ Generate Institutional Signal", callback_data="gen_signal")],
            [InlineKeyboardButton(text="📢 Auto-Post to My Trading Channel", callback_data="instructions")],
        ]
    )
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data == "home")
async def cb_home(callback: CallbackQuery):
    text = (
        "⚡ <b>Welcome to VENOM LIVE FOREX VIP BOT</b>\n\n"
        "Real-time live Smart Money Concepts (SMC) signals for Forex, Gold (XAU/USD), and Crypto backed by live market feeds.\n\n"
        "🚀 <b>Features:</b>\n"
        "• 100% Live Market Prices (ECB / CoinGecko Live Feed)\n"
        "• High-Probability Setups: Entry, SL, TP1, TP2, TP3\n"
        "• SMC Technical Rationale & Liquidity Sweep Analysis\n"
        "• Automated Signal Broadcasting for Telegram Channels\n\n"
        "Tap below to get an instant institutional signal:"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚡ Generate Institutional Signal", callback_data="gen_signal")],
            [InlineKeyboardButton(text="📢 Auto-Post to My Trading Channel", callback_data="instructions")],
        ]
    )
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "gen_signal")
async def cb_gen_signal(callback: CallbackQuery):
    signal_text = await LiveMarketEngine.generate_real_institutional_signal()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔄 Analyze Next Live Asset", callback_data="gen_signal")]]
    )
    await callback.message.answer(signal_text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "instructions")
async def cb_instructions(callback: CallbackQuery):
    text = (
        "📢 <b>How to Enable Auto-Posting to Your Trading Channel:</b>\n\n"
        "1. Open your Telegram Channel settings ➡️ <b>Administrators</b>.\n"
        "2. Add <b>@venom_forex_signals_bot</b> as an Admin with <i>'Post Messages'</i> permission.\n"
        "3. Once added, forward any message from your channel here.\n"
        "4. The bot will automatically broadcast live VIP signals to your channel! ⚡️"
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
            channel_title = event.chat.title or "Forex Channel"
            user_id = event.from_user.id
            async with AsyncSessionLocal() as session:
                existing = await session.execute(select(ConnectedChannel).where(ConnectedChannel.channel_id == channel_id))
                obj = existing.scalar_one_or_none()
                if not obj:
                    obj = ConnectedChannel(channel_id=channel_id, channel_title=channel_title, added_by=user_id, auto_post=True)
                    session.add(obj)
                    await session.commit()
            logger.info(f"Connected forex channel: {channel_title} ({channel_id})")
            try:
                welcome_post = (
                    f"⚡️ <b>Venom Forex VIP Auto-Poster Connected!</b>\n\n"
                    f"This channel is now connected to live institutional Forex, Gold, and Crypto SMC trading signals.\n\n"
                    f"Signals will be broadcasted automatically during market sessions! 📈"
                )
                await bot.send_message(chat_id=channel_id, text=welcome_post, parse_mode="HTML")
            except Exception as e:
                logger.warning(f"Failed to send welcome message: {e}")

# Link via forward
@dp.message(F.forward_from_chat)
async def handle_forward_link(message: Message):
    if message.forward_from_chat.type == "channel":
        ch_id = message.forward_from_chat.id
        ch_title = message.forward_from_chat.title or "Trading Channel"
        async with AsyncSessionLocal() as session:
            existing = await session.execute(select(ConnectedChannel).where(ConnectedChannel.channel_id == ch_id))
            obj = existing.scalar_one_or_none()
            if not obj:
                obj = ConnectedChannel(channel_id=ch_id, channel_title=ch_title, added_by=message.from_user.id, auto_post=True)
                session.add(obj)
                await session.commit()
        await message.answer(f"✅ <b>Successfully connected:</b> {ch_title}\nLive signal broadcasting is now active!", parse_mode="HTML")

# Background auto-poster loop (posts every 4 hours)
async def auto_signal_broadcaster():
    while True:
        try:
            async with AsyncSessionLocal() as session:
                res = await session.execute(select(ConnectedChannel).where(ConnectedChannel.auto_post == True))
                channels = res.scalars().all()
                if channels:
                    signal = await LiveMarketEngine.generate_real_institutional_signal()
                    for ch in channels:
                        try:
                            await bot.send_message(chat_id=ch.channel_id, text=signal, parse_mode="HTML")
                            logger.info(f"Auto-broadcasted signal to {ch.channel_title} ({ch.channel_id})")
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
