import asyncio
import re
import logging
from telethon import TelegramClient
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BotFatherAutomation")

async def create_new_bot(bot_name: str, preferred_username: str) -> dict:
    client = TelegramClient(settings.SESSION_NAME, settings.API_ID, settings.API_HASH)
    await client.start(phone=settings.PHONE_NUMBER)

    logger.info(f"Connecting to @BotFather to create '{bot_name}'...")
    
    async with client.conversation("@BotFather", timeout=45) as conv:
        # Step 1: Send /newbot
        await conv.send_message("/newbot")
        resp1 = await conv.get_response()
        logger.info(f"BotFather 1: {resp1.text}")

        # Step 2: Send Bot Name
        await conv.send_message(bot_name)
        resp2 = await conv.get_response()
        logger.info(f"BotFather 2: {resp2.text}")

        # Step 3: Try username variations
        username_attempts = [
            preferred_username,
            f"{preferred_username}_official_bot",
            f"venom_{preferred_username}",
            f"the_{preferred_username}",
            f"{preferred_username}1_bot",
        ]

        token = None
        final_username = None

        for uname in username_attempts:
            if not uname.endswith("bot") and not uname.endswith("Bot"):
                uname = f"{uname}_bot"

            logger.info(f"Trying username: @{uname}...")
            await conv.send_message(uname)
            resp3 = await conv.get_response()
            logger.info(f"BotFather 3: {resp3.text}")

            if "Done! Congratulations on your new bot" in resp3.text or "Use this token to access the HTTP API:" in resp3.text:
                # Extract token
                token_match = re.search(r"[0-9]{8,10}:[a-zA-Z0-9_-]{35}", resp3.text)
                if token_match:
                    token = token_match.group(0)
                    final_username = uname
                    break
            elif "Sorry, this username is already taken" in resp3.text or "occupied" in resp3.text:
                logger.warning(f"Username @{uname} is taken. Trying next variation...")
                continue
            else:
                logger.warning(f"Unexpected response: {resp3.text}")

    await client.disconnect()

    if token:
        logger.info(f"🎉 Bot created successfully! Username: @{final_username} | Token: {token}")
        return {"status": "success", "username": final_username, "token": token}
    else:
        return {"status": "error", "message": "Could not extract token"}

if __name__ == "__main__":
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else "Venom Forex Signals"
    uname = sys.argv[2] if len(sys.argv) > 2 else "venom_forex_signals"
    asyncio.run(create_new_bot(name, uname))
