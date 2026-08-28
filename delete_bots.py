import asyncio
import logging
from telethon import TelegramClient
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BotDeleter")

BOTS_TO_DELETE = ["@venom_forex_signals_bot", "@venomeaglebot"]

async def delete_bots():
    client = TelegramClient(settings.SESSION_NAME, settings.API_ID, settings.API_HASH)
    await client.start(phone=settings.PHONE_NUMBER)

    for bot_username in BOTS_TO_DELETE:
        logger.info(f"Connecting to @BotFather to delete {bot_username}...")
        try:
            async with client.conversation("@BotFather", timeout=45) as conv:
                await conv.send_message("/deletebot")
                resp1 = await conv.get_response()
                logger.info(f"BotFather 1: {resp1.text}")

                await asyncio.sleep(2)
                await conv.send_message(bot_username)
                resp2 = await conv.get_response()
                logger.info(f"BotFather 2: {resp2.text}")

                await asyncio.sleep(2)
                confirm_phrase = "Yes, I am totally sure."
                await conv.send_message(confirm_phrase)
                resp3 = await conv.get_response()
                logger.info(f"BotFather Final: {resp3.text}")

                if "Done! The bot is gone." in resp3.text or "deleted" in resp3.text.lower():
                    logger.info(f"🗑️ Successfully deleted {bot_username}!")
                else:
                    logger.warning(f"Response for {bot_username}: {resp3.text}")
        except Exception as e:
            logger.error(f"Error deleting {bot_username}: {e}")

        await asyncio.sleep(5)

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(delete_bots())
