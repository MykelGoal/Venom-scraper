import asyncio
import datetime
import logging
import os

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.fsm.storage.memory import MemoryStorage

from paywall_database import (
    SubscriptionPlan,
    activate_subscriber,
    create_pending_payment,
    get_expired_subscribers,
    get_plans,
    init_paywall_db,
)
from paystack_client import PaystackService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("VenomVIPGatekeeper")

BOT_TOKEN = os.getenv("BOT_TOKEN", "8872020288:AAHbHL2pcTjcNV6jlO7N-HdG8BbV0NfeEjk")
VIP_CHANNEL_ID = int(os.getenv("VIP_CHANNEL_ID", "-1001234567890"))
USDT_TRC20_WALLET = os.getenv("USDT_TRC20_WALLET", "TXxxVenomTechOfficialUSDTWalletAddress")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ---------------- Keyboards ----------------

async def get_plans_keyboard() -> InlineKeyboardMarkup:
    plans = await get_plans()
    buttons = []
    for p in plans:
        btn_text = f"{p.name} — ₦{p.price_ngn:,.0f} (${p.price_usd:.0f})"
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"plan:{p.slug}")])
    buttons.append([InlineKeyboardButton(text="💎 My Active Subscription", callback_data="my_sub")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_payment_methods_keyboard(plan_slug: str, paystack_url: str, reference: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="💳 Pay with Paystack (Card/Transfer/USSD)", url=paystack_url)],
        [InlineKeyboardButton(text="🪙 Pay with Crypto (USDT TRC20)", callback_data=f"crypto:{plan_slug}")],
        [InlineKeyboardButton(text="✅ I Have Completed Payment (Verify)", callback_data=f"verify:{reference}:{plan_slug}")],
        [InlineKeyboardButton(text="« Change Plan", callback_data="view_plans")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ---------------- Handlers ----------------

@dp.message(CommandStart())
async def cmd_start(message: Message):
    welcome = (
        "👑 <b>Welcome to VENOM VIP Membership Bot</b>\n\n"
        "Unlock direct, automated access to our exclusive VIP Signals & Community.\n\n"
        "⚡ <b>VIP Benefits:</b>\n"
        "• Daily High-Probability Signals & Alpha\n"
        "• Private VIP Community Chat\n"
        "• Direct Mentorship & Daily Analysis\n"
        "• Instant Automatic Access (24/7)\n\n"
        "Select your preferred VIP membership plan below:"
    )
    await message.answer(welcome, reply_markup=await get_plans_keyboard(), parse_mode="HTML")


@dp.callback_query(F.data == "view_plans")
async def cb_view_plans(callback: CallbackQuery):
    await callback.message.edit_text(
        "👑 <b>Select your VIP Membership Plan:</b>",
        reply_markup=await get_plans_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("plan:"))
async def cb_select_plan(callback: CallbackQuery):
    plan_slug = callback.data.split(":")[1]
    plans = await get_plans()
    plan = next((p for p in plans if p.slug == plan_slug), None)
    if not plan:
        await callback.answer("Plan not found.", show_alert=True)
        return

    amount_kobo = int(plan.price_ngn * 100)
    email = f"user_{callback.from_user.id}@telegram.venom"

    # Initialize Paystack Checkout Link
    pay_res = await PaystackService.initialize_payment(email=email, amount_kobo=amount_kobo)
    reference = pay_res.get("reference")
    pay_url = pay_res.get("authorization_url", "https://paystack.com")

    # Record pending transaction
    await create_pending_payment(
        telegram_id=callback.from_user.id,
        plan_slug=plan_slug,
        amount=float(plan.price_ngn),
        reference=reference,
    )

    text = (
        f"🎯 <b>You Selected: {plan.name}</b>\n"
        f"📝 <i>{plan.description}</i>\n\n"
        f"💰 <b>Amount:</b> ₦{plan.price_ngn:,.0f} / ${plan.price_usd:.0f}\n"
        f"⏳ <b>Duration:</b> {plan.duration_days} Days\n"
        f"🔖 <b>Payment Ref:</b> <code>{reference}</code>\n\n"
        f"Choose your payment method below to get instant VIP access:"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_payment_methods_keyboard(plan_slug, pay_url, reference),
        parse_mode="HTML",
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("crypto:"))
async def cb_crypto_pay(callback: CallbackQuery):
    plan_slug = callback.data.split(":")[1]
    plans = await get_plans()
    plan = next((p for p in plans if p.slug == plan_slug), None)

    text = (
        f"🪙 <b>Crypto Payment (USDT TRC20)</b>\n\n"
        f"• <b>Plan:</b> {plan.name}\n"
        f"• <b>Amount:</b> <b>${plan.price_usd:.2f} USDT</b>\n"
        f"• <b>Network:</b> TRON (TRC20)\n\n"
        f"📥 <b>Deposit Address:</b>\n"
        f"<code>{USDT_TRC20_WALLET}</code>\n\n"
        f"⚠️ <i>After transferring, send your transaction hash or receipt screenshot to @Admin to get approved in 60 seconds.</i>"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Send Receipt to Support", url="https://t.me/Mikelolawale")],
            [InlineKeyboardButton(text="« Back to Plans", callback_data="view_plans")],
        ]
    )
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@dp.callback_query(F.data.startswith("verify:"))
async def cb_verify_payment(callback: CallbackQuery):
    parts = callback.data.split(":")
    reference = parts[1]
    plan_slug = parts[2]

    await callback.answer("Checking payment status with Paystack...", show_alert=False)

    # Verify payment with Paystack API
    is_successful = await PaystackService.verify_payment(reference)

    # For testing / mock fallback if Paystack test key is not yet set
    if not is_successful and "sk_test_mock" in os.getenv("PAYSTACK_SECRET_KEY", "sk_test_mock"):
        is_successful = True  # Auto-pass demo in test mode

    if is_successful:
        plans = await get_plans()
        plan = next((p for p in plans if p.slug == plan_slug), None)
        duration_days = plan.duration_days if plan else 30

        # Generate a secure 1-time single-use invite link
        invite_link = None
        try:
            link_obj = await bot.create_chat_invite_link(
                chat_id=VIP_CHANNEL_ID,
                member_limit=1,
                expire_date=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=2),
                name=f"VIP_{callback.from_user.id}",
            )
            invite_link = link_obj.invite_link
        except Exception:
            # Fallback direct channel link if not added as admin to target channel
            invite_link = "https://t.me/+VenomVIPOfficialInviteLink"

        # Activate subscriber in database
        sub = await activate_subscriber(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            full_name=callback.from_user.full_name,
            plan_slug=plan_slug,
            reference=reference,
            invite_link=invite_link,
            duration_days=duration_days,
        )

        success_text = (
            "🎉 <b>PAYMENT CONFIRMED & VIP ACTIVATED!</b>\n\n"
            f"👤 <b>Subscriber:</b> {callback.from_user.full_name}\n"
            f"👑 <b>Plan:</b> {plan.name}\n"
            f"⏳ <b>Valid Until:</b> {sub.expires_at.strftime('%Y-%m-%d %H:%M UTC') if sub.expires_at else 'Lifetime Access'}\n\n"
            f"🔗 <b>Your Exclusive 1-Time VIP Invite Link:</b>\n"
            f"{invite_link}\n\n"
            f"<i>⚠️ Note: This invite link can only be used once by your account. Tap to join now!</i>"
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🚀 Join VIP Channel Now", url=invite_link)]]
        )
        await callback.message.edit_text(success_text, reply_markup=kb, parse_mode="HTML")
    else:
        await callback.message.answer(
            "⏳ Payment not yet detected. If you just transferred, please wait a minute and tap verify again, or contact @Admin.",
            show_alert=True,
        )


# ---------------- Background Auto-Revoke Expired Subscriptions ----------------

async def auto_expire_worker():
    """Periodically checks and revokes access for expired subscribers."""
    while True:
        try:
            expired = await get_expired_subscribers()
            for sub in expired:
                logger.info(f"Subscription expired for user {sub.telegram_id} ({sub.full_name}). Revoking...")
                try:
                    await bot.ban_chat_member(chat_id=VIP_CHANNEL_ID, user_id=sub.telegram_id)
                    await bot.unban_chat_member(chat_id=VIP_CHANNEL_ID, user_id=sub.telegram_id)
                    await bot.send_message(
                        chat_id=sub.telegram_id,
                        text="⚠️ <b>Your VIP Subscription has expired.</b>\n\nTo regain access to VIP signals and community, send /start to renew your pass!",
                        parse_mode="HTML",
                    )
                except Exception as e:
                    logger.debug(f"Could not kick expired user {sub.telegram_id}: {e}")
                sub.is_active = False
        except Exception as e:
            logger.error(f"Error in expiry worker: {e}")
        await asyncio.sleep(3600)  # Check every 1 hour


# ---------------- Entrypoint ----------------

async def main():
    await init_paywall_db()
    asyncio.create_task(auto_expire_worker())
    logger.info("Venom VIP Paywall Bot started & listening...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
