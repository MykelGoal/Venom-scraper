import asyncio
import json
import sys
from telethon import TelegramClient
from config import settings

async def send_code():
    client = TelegramClient(settings.SESSION_NAME, settings.API_ID, settings.API_HASH)
    await client.connect()
    
    if await client.is_user_authorized():
        me = await client.get_me()
        print(f"ALREADY_AUTHORIZED:@{me.username or me.id}:{me.first_name}")
        await client.disconnect()
        return

    phone = settings.PHONE_NUMBER
    print(f"Requesting Telegram login code for {phone}...")
    try:
        sent_code = await client.send_code_request(phone)
        with open("auth_state.json", "w") as f:
            json.dump({
                "phone": phone,
                "phone_code_hash": sent_code.phone_code_hash
            }, f)
        print("CODE_SENT_SUCCESSFULLY")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(send_code())
