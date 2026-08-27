import asyncio
from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault
from config import settings

async def setup_bot():
    if not settings.BOT_TOKEN:
        print("Error: BOT_TOKEN is missing from .env")
        return

    bot = Bot(token=settings.BOT_TOKEN)

    # 1. Set Bot Commands
    commands = [
        BotCommand(command="start", description="🏠 Open Main Menu & Browse Categories"),
        BotCommand(command="search", description="🔍 Search members by keyword (/search <query>)"),
        BotCommand(command="categories", description="📂 Browse directory by niche"),
        BotCommand(command="discover", description="🚀 Auto-discover & deep scan groups (/discover <query>)"),
        BotCommand(command="stats", description="📊 View directory statistics"),
        BotCommand(command="about", description="ℹ️ About directory & privacy policy"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    print("✅ Bot commands updated successfully.")

    # 2. Set Bot Description (shown in empty chat before user presses Start)
    description = (
        "🕷️ VENOM SCRAPER — High-Performance Public Telegram Directory & Member Discovery Engine.\n\n"
        "✨ What this bot does:\n"
        "• 🔍 Search active public members across top niches (Betting, Crypto, Tech, Gaming, Marketing)\n"
        "• 📂 Browse verified public groups & categories\n"
        "• 🔗 Clickable direct t.me profile links\n"
        "• 🚀 Deep scan & auto-discovery of public communities\n\n"
        "Press 'Start' below to begin exploring the directory!"
    )
    await bot.set_my_description(description=description)
    print("✅ Bot description (intro screen) updated successfully.")

    # 3. Set Bot Short Description (shown on profile / shared links)
    short_description = "🕷️ VENOM SCRAPER: Search active public members & communities by niche, username, and category."
    await bot.set_my_short_description(short_description=short_description)
    print("✅ Bot short description (bio) updated successfully.")

    # 4. Set Bot Name
    await bot.set_my_name(name="VENOM SCRAPER")
    print("✅ Bot name confirmed as 'VENOM SCRAPER'.")

    me = await bot.get_me()
    print("\n" + "=" * 60)
    print(f"🎉 Bot Profile Configuration Complete!")
    print(f"Bot Name        : {me.first_name}")
    print(f"Bot Username    : @{me.username}")
    print(f"Bot ID          : {me.id}")
    print("=" * 60)

    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(setup_bot())
