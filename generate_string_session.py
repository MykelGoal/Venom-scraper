import asyncio
import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from config import settings

async def generate():
    print("=" * 60)
    print(" 🔑 TELEGRAM STRING SESSION GENERATOR (For Render / Cloud)")
    print("=" * 60)
    print(f"API_ID: {settings.API_ID}")
    print(f"API_HASH: {settings.API_HASH[:6]}...{settings.API_HASH[-4:]}")
    print()

    # Create client with empty StringSession
    client = TelegramClient(StringSession(), settings.API_ID, settings.API_HASH)
    await client.start(phone=settings.PHONE_NUMBER)

    session_string = client.session.save()
    me = await client.get_me()

    print("\n" + "=" * 60)
    print(" 🎉 STRING SESSION GENERATED SUCCESSFULLY!")
    print(f" Logged in as: {me.first_name} (@{me.username or 'No username'})")
    print("=" * 60)
    print("\nCopy the STRING_SESSION below and paste it into your Render Environment Variables:\n")
    print(f"TELEGRAM_STRING_SESSION={session_string}")
    print("\n" + "=" * 60)

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(generate())
