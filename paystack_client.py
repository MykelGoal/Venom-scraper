import aiohttp
import os
import secrets
import logging

logger = logging.getLogger("PaystackClient")

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "sk_test_mock_secret_key")

class PaystackService:
    BASE_URL = "https://api.paystack.co"

    @classmethod
    async def initialize_payment(cls, email: str, amount_kobo: int, callback_url: str = None) -> dict:
        """
        Initializes a Paystack transaction.
        amount_kobo: amount in Kobo (NGN 5,000 = 500,000 Kobo)
        """
        reference = f"VENOM_{secrets.token_hex(8)}"
        headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "email": email,
            "amount": amount_kobo,
            "reference": reference,
        }
        if callback_url:
            payload["callback_url"] = callback_url

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{cls.BASE_URL}/transaction/initialize", json=payload, headers=headers) as resp:
                    data = await resp.json()
                    if data.get("status"):
                        return {
                            "status": "success",
                            "authorization_url": data["data"]["authorization_url"],
                            "access_code": data["data"]["access_code"],
                            "reference": reference,
                        }
                    else:
                        logger.warning(f"Paystack init failed: {data.get('message')}")
                        return {"status": "error", "message": data.get("message"), "reference": reference}
        except Exception as e:
            logger.error(f"Paystack network error: {e}")
            return {"status": "error", "message": str(e), "reference": reference}

    @classmethod
    async def verify_payment(cls, reference: str) -> bool:
        """Verifies transaction reference with Paystack API."""
        headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{cls.BASE_URL}/transaction/verify/{reference}", headers=headers) as resp:
                    data = await resp.json()
                    if data.get("status") and data.get("data", {}).get("status") == "success":
                        return True
                    return False
        except Exception as e:
            logger.error(f"Paystack verification error: {e}")
            return False
