import asyncio
from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault

FOREX_TOKEN = "8648284351:AAEZlL9WviiYXQRte1tJpJ3E1HJK2VsBAXU"
EAGLE_TOKEN = "8817389005:AAE1EsYKv1fC9GwntH8x4ILCNZ7bRzTXP14"

async def setup_forex_profile():
    bot = Bot(token=FOREX_TOKEN)
    commands = [
        BotCommand(command="start", description="⚡ Start & Generate Live Forex Setup"),
        BotCommand(command="signal", description="📊 Get Institutional Trade Analysis"),
        BotCommand(command="autopost", description="📢 How to auto-post to your trading channel"),
        BotCommand(command="about", description="ℹ️ About Venom Institutional Signals"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    
    desc = (
        "⚡ VENOM INSTITUTIONAL FOREX & GOLD SIGNALS ⚡\n\n"
        "Institutional Smart Money Concepts (SMC) signals for Forex, Gold (XAU/USD), and Bitcoin.\n\n"
        "🚀 Features:\n"
        "• High-Probability Setups with Entry, TP1, TP2, Stop Loss\n"
        "• SMC Technical Rationale & Liquidity Sweep Insights\n"
        "• Auto-Post Bot for Telegram Trading Channels\n\n"
        "Press 'Start' below to generate your first institutional signal!"
    )
    await bot.set_my_description(description=desc)
    await bot.set_my_short_description(short_description="⚡ High-probability institutional Forex, Gold & Crypto signals with SMC analysis.")
    await bot.set_my_name(name="Venom Forex Signals")
    await bot.session.close()
    print("✅ Venom Forex Bot profile setup complete!")

async def setup_eagle_profile():
    bot = Bot(token=EAGLE_TOKEN)
    commands = [
        BotCommand(command="start", description="🦅 Start & Generate Daily Banker Intelligence"),
        BotCommand(command="banker", description="🎯 Get High-Confidence Match Pick & Odds"),
        BotCommand(command="codes", description="🎟️ SportyBet, Bet9ja & 1xBet Booking Codes"),
        BotCommand(command="autopost", description="📢 How to auto-post to your betting channel"),
        BotCommand(command="about", description="ℹ️ About Venom Eagle AI Engine"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())

    desc = (
        "🦅 VENOM EAGLE AI — FOOTBALL MATCH INTELLIGENCE 🦅\n\n"
        "EaglePredict-style match analysis, AI banker predictions, and instant booking codes.\n\n"
        "🎯 Features:\n"
        "• Daily Banker of the Day (>85% Win Probability)\n"
        "• Tactical Breakdown, Form Guides & H2H Stats\n"
        "• Live SportyBet, Bet9ja & 1xBet Booking Codes\n"
        "• Auto-Poster Bot for Betting Channels\n\n"
        "Press 'Start' below to analyze today's banker match!"
    )
    await bot.set_my_description(description=desc)
    await bot.set_my_short_description(short_description="🦅 Eagle-style match intelligence, AI banker predictions & live SportyBet booking codes.")
    await bot.set_my_name(name="Venom Eagle Predictions")
    await bot.session.close()
    print("✅ Venom Eagle Predictions Bot profile setup complete!")

async def main():
    await setup_forex_profile()
    await setup_eagle_profile()

if __name__ == "__main__":
    asyncio.run(main())
