import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from config import settings

async def convert():
    # Load existing file session
    client = TelegramClient(settings.SESSION_NAME, settings.API_ID, settings.API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        print("Session is not authorized. Please run auth_session.py first.")
        await client.disconnect()
        return

    me = await client.get_me()
    # Export to StringSession
    string_sess = StringSession.save(client.session)
    print(f"STRING_SESSION_VALUE:{string_sess}")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(convert())
