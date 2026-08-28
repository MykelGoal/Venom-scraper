import asyncio
import os
from telethon import TelegramClient
from config import settings

async def upload_avatar():
    client = TelegramClient(settings.SESSION_NAME, settings.API_ID, settings.API_HASH)
    await client.start(phone=settings.PHONE_NUMBER)

    print("Connecting to @BotFather to update profile picture...")
    async with client.conversation("@BotFather", timeout=30) as conv:
        # Step 1: Send /setuserpic
        await conv.send_message("/setuserpic")
        resp1 = await conv.get_response()
        print(f"BotFather: {resp1.text}")

        # Step 2: Choose bot
        await conv.send_message("@venomscraperbot")
        resp2 = await conv.get_response()
        print(f"BotFather: {resp2.text}")

        # Step 3: Send photo
        avatar_path = "bot_avatar.png"
        if not os.path.exists(avatar_path):
            print(f"Error: {avatar_path} not found!")
            return

        print(f"Sending photo '{avatar_path}'...")
        await conv.send_file(avatar_path)
        resp3 = await conv.get_response()
        print(f"\nBotFather Final Response:\n{resp3.text}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(upload_avatar())
