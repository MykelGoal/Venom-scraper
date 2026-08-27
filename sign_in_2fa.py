import asyncio
import sys
from telethon import TelegramClient
from config import settings

async def sign_in_2fa(password: str):
    client = TelegramClient(settings.SESSION_NAME, settings.API_ID, settings.API_HASH)
    await client.connect()

    try:
        if await client.is_user_authorized():
            me = await client.get_me()
            print(f"ALREADY_AUTHORIZED:@{me.username or me.id}:{me.first_name}")
            return

        print("Submitting 2FA password...")
        await client.sign_in(password=password)
        me = await client.get_me()
        print(f"SUCCESS:@{me.username or me.id}:{me.first_name}")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
    finally:
        await client.disconnect()

if __name__ == "__main__":
    pw = sys.argv[1] if len(sys.argv) > 1 else ""
    asyncio.run(sign_in_2fa(pw))
