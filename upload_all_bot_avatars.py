import asyncio
import os
import logging
from telethon import TelegramClient
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AvatarUploader")

BOTS_TO_UPDATE = [
    {
        "username": "@venom_forex_signals_bot",
        "avatar": "venom_forex_avatar.png",
    },
    {
        "username": "@venomeaglebot",
        "avatar": "venom_eagle_avatar.png",
    },
]

async def upload_avatars():
    client = TelegramClient(settings.SESSION_NAME, settings.API_ID, settings.API_HASH)
    await client.start(phone=settings.PHONE_NUMBER)

    for item in BOTS_TO_UPDATE:
        uname = item["username"]
        pic = item["avatar"]

        if not os.path.exists(pic):
            logger.error(f"Image {pic} not found!")
            continue

        logger.info(f"Setting profile picture for {uname} with {pic}...")
        try:
            async with client.conversation("@BotFather", timeout=30) as conv:
                await conv.send_message("/setuserpic")
                resp1 = await conv.get_response()
                logger.info(f"BotFather: {resp1.text}")

                await asyncio.sleep(2)
                await conv.send_message(uname)
                resp2 = await conv.get_response()
                logger.info(f"BotFather: {resp2.text}")

                await asyncio.sleep(2)
                await conv.send_file(pic)
                resp3 = await conv.get_response()
                logger.info(f"BotFather Final: {resp3.text}")
        except Exception as e:
            logger.error(f"Failed to upload for {uname}: {e}")

        await asyncio.sleep(5)

    await client.disconnect()
    logger.info("Avatar upload process completed!")

if __name__ == "__main__":
    asyncio.run(upload_avatars())
