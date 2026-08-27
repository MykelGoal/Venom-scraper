import asyncio
import json
import sys
from telethon import TelegramClient, errors
from config import settings

async def verify(code: str, password: str = None):
    if not code:
        print("ERROR: No code provided", file=sys.stderr)
        return

    with open("auth_state.json", "r") as f:
        auth_state = json.load(f)

    phone = auth_state["phone"]
    phone_code_hash = auth_state["phone_code_hash"]

    client = TelegramClient(settings.SESSION_NAME, settings.API_ID, settings.API_HASH)
    await client.connect()

    try:
        try:
            await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
        except errors.SessionPasswordNeededError:
            if not password:
                print("2FA_PASSWORD_REQUIRED")
                await client.disconnect()
                return
            await client.sign_in(password=password)

        me = await client.get_me()
        print(f"SUCCESS:@{me.username or me.id}:{me.first_name}")
    except Exception as e:
        print(f"AUTH_ERROR: {e}", file=sys.stderr)
    finally:
        await client.disconnect()

if __name__ == "__main__":
    code_arg = sys.argv[1] if len(sys.argv) > 1 else ""
    pw_arg = sys.argv[2] if len(sys.argv) > 2 else None
    asyncio.run(verify(code_arg, pw_arg))
