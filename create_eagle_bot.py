import asyncio
import re
import logging
from telethon import TelegramClient
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BotFatherCreator")

async def create_bot_safe(bot_name: str, preferred_usernames: list):
    client = TelegramClient(settings.SESSION_NAME, settings.API_ID, settings.API_HASH)
    await client.start(phone=settings.PHONE_NUMBER)

    logger.info("Waiting 10s for BotFather cooldown...")
    await asyncio.sleep(10)

    async with client.conversation("@BotFather", timeout=45) as conv:
        await conv.send_message("/newbot")
        resp1 = await conv.get_response()
        logger.info(f"BotFather: {resp1.text}")

        await asyncio.sleep(2)
        await conv.send_message(bot_name)
        resp2 = await conv.get_response()
        logger.info(f"BotFather: {resp2.text}")

        token = None
        final_uname = None

        for uname in preferred_usernames:
            await asyncio.sleep(2)
            logger.info(f"Sending username: @{uname}...")
            await conv.send_message(uname)
            resp3 = await conv.get_response()
            logger.info(f"BotFather: {resp3.text}")

            if "Done! Congratulations on your new bot" in resp3.text or "Use this token" in resp3.text:
                token_match = re.search(r"[0-9]{8,10}:[a-zA-Z0-9_-]{35}", resp3.text)
                if token_match:
                    token = token_match.group(0)
                    final_uname = uname
                    break
            elif "already taken" in resp3.text:
                continue
            else:
                break

    await client.disconnect()
    if token:
        print(f"\nSUCCESS: @{final_uname} created with token: {token}")
        return final_uname, token
    else:
        print("\nFailed to create bot.")
        return None, None

if __name__ == "__main__":
    asyncio.run(create_bot_safe(
        "Venom Eagle Predictions",
        ["venomeaglebot", "venomeagle_bot", "venom_eagle_betbot", "venomeagleprediction_bot", "venomeagle_banker_bot"]
    ))
