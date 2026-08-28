import asyncio
from telethon import TelegramClient
from config import settings

async def check_mybots():
    client = TelegramClient(settings.SESSION_NAME, settings.API_ID, settings.API_HASH)
    await client.start(phone=settings.PHONE_NUMBER)

    async with client.conversation("@BotFather", timeout=30) as conv:
        await conv.send_message("/mybots")
        resp = await conv.get_response()
        print(f"BotFather response:\n{resp.text}")
        if resp.buttons:
            print("Buttons:")
            for row in resp.buttons:
                for btn in row:
                    print(f" - {btn.text} (data={btn.data})")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(check_mybots())
