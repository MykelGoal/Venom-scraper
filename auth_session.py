import asyncio
import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID", 22451514))
API_HASH = os.getenv("API_HASH", "d5dff7cdc6a0501fcf3d8af3afc69563")

async def test_auth():
    print("=" * 60)
    print(" Telegram MTProto Userbot Authentication Helper")
    print("=" * 60)
    print(f"Using API_ID: {API_ID}")
    print(f"Using API_HASH: {API_HASH[:6]}...{API_HASH[-4:]}")
    print()

    client = TelegramClient("tg_indexer_session", API_ID, API_HASH)
    
    # client.start() prompts for phone number, login code, and 2FA password if needed
    await client.start()

    me = await client.get_me()
    print("\n" + "=" * 60)
    print(" Authentication Successful!")
    print(f" Logged in as: {me.first_name} (@{me.username or 'No username'})")
    print(f" Telegram User ID: {me.id}")
    print(f" Session file saved as: tg_indexer_session.session")
    print("=" * 60)

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_auth())
