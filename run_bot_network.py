import asyncio
import logging
import os
from aiogram import Bot

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("VenomNetworkManager")

async def start_scraper_bot():
    try:
        from bot import dp, init_db, seed_default_categories
        from seed_manager import seed_from_file_if_empty
        from config import settings
        await init_db()
        await seed_default_categories()
        await seed_from_file_if_empty()
        bot = Bot(token=settings.BOT_TOKEN)
        logger.info("🤖 Venom Scraper Bot started polling (@venomscraperbot)...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error in Scraper Bot: {e}")

async def start_forex_bot():
    try:
        from forex_bot import dp as forex_dp, init_db as init_forex_db, BOT_TOKEN as forex_token, auto_signal_broadcaster
        await init_forex_db()
        bot = Bot(token=forex_token)
        asyncio.create_task(auto_signal_broadcaster())
        logger.info("⚡ Venom Forex Signals Bot started polling (@venom_forex_signals_bot)...")
        await forex_dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error in Forex Bot: {e}")

async def start_prediction_bot():
    try:
        from prediction_bot import dp as pred_dp, init_db as init_pred_db, BOT_TOKEN as pred_token, auto_prediction_broadcaster
        await init_pred_db()
        bot = Bot(token=pred_token)
        asyncio.create_task(auto_prediction_broadcaster())
        logger.info("🦅 Venom Eagle Predictions Bot started polling (@venomeaglebot)...")
        await pred_dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error in Eagle Prediction Bot: {e}")

async def main():
    logger.info("=" * 65)
    logger.info("🕷️ LAUNCHING VENOM TECH MULTI-BOT ECOSYSTEM NETWORK")
    logger.info("=" * 65)

    # Start Uptime Web Server
    try:
        from uptime_server import start_uptime_web_server
        await start_uptime_web_server(port=int(os.getenv("PORT", 8080)))
    except Exception as e:
        logger.warning(f"Uptime server notice: {e}")

    await asyncio.gather(
        start_scraper_bot(),
        start_forex_bot(),
        start_prediction_bot(),
    )

if __name__ == "__main__":
    asyncio.run(main())
