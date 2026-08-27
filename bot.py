import asyncio
import logging
import math
from typing import Optional

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    CallbackQuery,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database import (
    get_all_categories,
    get_directory_stats,
    init_db,
    search_directory,
    seed_default_categories,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("TG_SearchBot")


class SearchState(StatesGroup):
    waiting_for_query = State()


# ---------------- Keyboards & UI Helpers ----------------

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="📂 Browse by Niche / Category", callback_data="menu:categories"),
        ],
        [
            InlineKeyboardButton(text="🔍 Search Members", callback_data="menu:search_prompt"),
            InlineKeyboardButton(text="📊 Directory Stats", callback_data="menu:stats"),
        ],
        [
            InlineKeyboardButton(text="ℹ️ About & Privacy", callback_data="menu:about"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_categories_keyboard() -> InlineKeyboardMarkup:
    categories = await get_all_categories()
    buttons = []
    for cat in categories:
        text = f"{cat['name']} ({cat['member_count']} members)"
        cb_data = f"cat:{cat['slug']}:1"
        buttons.append([InlineKeyboardButton(text=text, callback_data=cb_data)])

    buttons.append([InlineKeyboardButton(text="« Back to Main Menu", callback_data="menu:home")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def format_member_card(member: dict, index: int) -> str:
    username = member["username"]
    name = f"{member['first_name']} {member['last_name']}".strip() or "Anonymous"
    categories = " ".join([f"#{c.replace(' ', '')}" for c in member["categories"]])
    groups = ", ".join(member["groups"][:2])
    status = member.get("last_seen", "unknown")

    return (
        f"👤 <b>{index}. {name}</b>\n"
        f"🔗 <b>Username:</b> @{username}\n"
        f"🏷️ <b>Niches:</b> {categories}\n"
        f"👥 <b>Found in:</b> {groups}\n"
        f"🕒 <b>Activity:</b> <i>{status}</i>\n"
        f"🌐 <b>Profile Link:</b> <a href=\"https://t.me/{username}\">t.me/{username}</a>\n"
    )


def build_pagination_keyboard(
    category_slug: Optional[str],
    query: Optional[str],
    current_page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:
    nav_buttons = []

    # Category or Keyword identifier for callback
    cb_prefix = f"page:cat={category_slug or ''}:q={query or ''}"

    if current_page > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Previous", callback_data=f"{cb_prefix}:{current_page - 1}")
        )

    nav_buttons.append(
        InlineKeyboardButton(text=f"📄 {current_page}/{max(1, total_pages)}", callback_data="noop")
    )

    if current_page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(text="Next ➡️", callback_data=f"{cb_prefix}:{current_page + 1}")
        )

    rows = [nav_buttons]
    rows.append([InlineKeyboardButton(text="📂 Browse Other Categories", callback_data="menu:categories")])
    rows.append([InlineKeyboardButton(text="🏠 Main Menu", callback_data="menu:home")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


# ---------------- Bot Handlers ----------------

dp = Dispatcher(storage=MemoryStorage())


@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    welcome_text = (
        f"👋 <b>Welcome to the Public Telegram Community Directory!</b>\n\n"
        f"This bot provides an organized directory of active members from public Telegram communities.\n\n"
        f"💡 <b>Features:</b>\n"
        f"• Search public members by username, keyword, or niche\n"
        f"• Filter by categories (Crypto, Gaming, Betting, Tech, etc.)\n"
        f"• Direct clickable <code>t.me/...</code> profile links\n"
        f"• Only indexes public usernames from public groups\n\n"
        f"Select an option below to begin:"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu_keyboard(), parse_mode="HTML")


@dp.message(Command("categories"))
async def cmd_categories(message: Message):
    kb = await get_categories_keyboard()
    await message.answer(
        "📂 <b>Select a Niche / Category:</b>\n\nBrowse members discovered in verified public communities:",
        reply_markup=kb,
        parse_mode="HTML",
    )


@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    stats = await get_directory_stats()
    text = (
        f"📊 <b>Directory Statistics</b>\n\n"
        f"👥 <b>Indexed Public Members:</b> {stats['total_members']:,}\n"
        f"📢 <b>Scanned Public Groups:</b> {stats['total_groups']:,}\n"
        f"🏷️ <b>Active Categories:</b> {stats['total_categories']:,}\n\n"
        f"<i>Updated dynamically with every scan.</i>"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="« Main Menu", callback_data="menu:home")]]
    )
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@dp.message(Command("about"))
async def cmd_about(message: Message):
    text = (
        f"ℹ️ <b>About & Privacy Policy</b>\n\n"
        f"• <b>Source:</b> Information is indexed exclusively from public Telegram groups with open participant visibility.\n"
        f"• <b>Data:</b> Only public <code>@username</code> handles and profile names are stored. No private chats, phone numbers, or hidden accounts are accessed.\n"
        f"• <b>Compliance:</b> Deleted accounts and bot accounts are automatically pruned.\n"
        f"• <b>Usage:</b> Intended for community discovery, networking, and public directory indexing."
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="« Main Menu", callback_data="menu:home")]]
    )
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@dp.callback_query(F.data == "menu:home")
async def cb_home(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "👋 <b>Public Telegram Community Directory</b>\n\nChoose an action below to find members across public niches:",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@dp.callback_query(F.data == "menu:categories")
async def cb_categories(callback: CallbackQuery):
    kb = await get_categories_keyboard()
    await callback.message.edit_text(
        "📂 <b>Select a Niche / Category:</b>\n\nBrowse members discovered in verified public communities:",
        reply_markup=kb,
        parse_mode="HTML",
    )
    await callback.answer()


@dp.callback_query(F.data == "menu:stats")
async def cb_stats(callback: CallbackQuery):
    stats = await get_directory_stats()
    text = (
        f"📊 <b>Directory Statistics</b>\n\n"
        f"👥 <b>Indexed Public Members:</b> {stats['total_members']:,}\n"
        f"📢 <b>Scanned Public Groups:</b> {stats['total_groups']:,}\n"
        f"🏷️ <b>Active Categories:</b> {stats['total_categories']:,}\n\n"
        f"<i>Updated dynamically with every scan.</i>"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="« Back", callback_data="menu:home")]]
    )
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@dp.callback_query(F.data == "menu:about")
async def cb_about(callback: CallbackQuery):
    text = (
        f"ℹ️ <b>About & Privacy Policy</b>\n\n"
        f"• <b>Source:</b> Information is indexed exclusively from public Telegram groups with open participant visibility.\n"
        f"• <b>Data:</b> Only public <code>@username</code> handles and profile names are stored. No private chats, phone numbers, or hidden accounts are accessed.\n"
        f"• <b>Compliance:</b> Deleted accounts and bot accounts are automatically pruned.\n"
        f"• <b>Usage:</b> Intended for community discovery, networking, and public directory indexing."
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="« Back", callback_data="menu:home")]]
    )
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@dp.callback_query(F.data == "menu:search_prompt")
async def cb_search_prompt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.waiting_for_query)
    text = (
        "🔍 <b>Search Public Directory</b>\n\n"
        "Please type a username, name, or keyword (e.g., <code>crypto_trader</code>, <code>Alex</code>, <code>developer</code>):\n"
        "Or use <code>/search &lt;query&gt;</code> anytime."
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="menu:home")]]
    )
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@dp.message(SearchState.waiting_for_query)
async def process_search_input(message: Message, state: FSMContext):
    query = message.text.strip()
    await state.clear()
    await execute_and_render_search(message, query=query, category_slug=None, page=1)


@dp.message(Command("search"))
async def cmd_search(message: Message, state: FSMContext):
    await state.clear()
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️ Please provide a search keyword. Example: <code>/search crypto</code>", parse_mode="HTML")
        return
    query = args[1].strip()
    await execute_and_render_search(message, query=query, category_slug=None, page=1)


@dp.callback_query(F.data.startswith("cat:"))
async def cb_category_members(callback: CallbackQuery):
    try:
        await callback.answer()
    except Exception:
        pass
    parts = callback.data.split(":")
    category_slug = parts[1]
    page = int(parts[2]) if len(parts) > 2 else 1
    await execute_and_render_search(callback.message, query=None, category_slug=category_slug, page=page, is_edit=True)


@dp.callback_query(F.data.startswith("page:"))
async def cb_pagination(callback: CallbackQuery):
    try:
        await callback.answer()
    except Exception:
        pass
    raw_parts = callback.data.split(":")
    cat_param = raw_parts[1].replace("cat=", "") or None
    q_param = raw_parts[2].replace("q=", "") or None
    target_page = int(raw_parts[3])

    await execute_and_render_search(
        callback.message,
        query=q_param,
        category_slug=cat_param,
        page=target_page,
        is_edit=True,
    )


@dp.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery):
    await callback.answer()


async def execute_and_render_search(
    message_or_target: Message,
    query: Optional[str] = None,
    category_slug: Optional[str] = None,
    page: int = 1,
    is_edit: bool = False,
):
    page_size = settings.SEARCH_PAGE_SIZE
    members, total_count = await search_directory(
        query=query,
        category_slug=category_slug,
        page=page,
        page_size=page_size,
    )

    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

    header = "🔍 <b>Search Results</b>\n"
    if category_slug:
        header = f"📂 <b>Category:</b> <code>#{category_slug}</code>\n"
    if query:
        header += f"🔎 <b>Query:</b> <i>'{query}'</i>\n"

    header += f"📊 <b>Found:</b> {total_count} members (Showing page {page} of {total_pages})\n\n"

    if not members:
        body = "<i>No matching members found. Try another search or category.</i>\n"
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📂 Browse Categories", callback_data="menu:categories")],
                [InlineKeyboardButton(text="🏠 Main Menu", callback_data="menu:home")],
            ]
        )
        final_text = header + body
    else:
        cards = []
        for idx, m in enumerate(members, start=(page - 1) * page_size + 1):
            cards.append(format_member_card(m, idx))

        body = "\n".join(cards)
        final_text = header + body
        kb = build_pagination_keyboard(category_slug, query, page, total_pages)

    if is_edit:
        try:
            await message_or_target.edit_text(final_text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)
        except Exception:
            pass
    else:
        await message_or_target.answer(final_text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)


@dp.message(Command("discover"))
async def cmd_discover(message: Message):
    # Check if admin or allow if admin list is empty
    if settings.ADMIN_IDS and message.from_user.id not in settings.ADMIN_IDS:
        await message.answer("⚠️ Admin permission required to trigger background group discovery.")
        return

    args = message.text.split(maxsplit=2)
    if len(args) < 2:
        await message.answer(
            "⚠️ <b>Usage:</b> <code>/discover &lt;query&gt; [category]</code>\n\n"
            "<b>Example:</b> <code>/discover crypto signals crypto</code>\n"
            "<b>Example:</b> <code>/discover sportybet betting</code>",
            parse_mode="HTML",
        )
        return

    query_term = args[1]
    category_term = args[2] if len(args) > 2 else "tech"

    status_msg = await message.answer(
        f"🔎 <b>Initiating Deep Search & Discovery</b>\n\n"
        f"• <b>Keywords:</b> <code>{query_term}</code>\n"
        f"• <b>Category:</b> <code>{category_term}</code>\n\n"
        f"<i>Scanning Telegram globally for open public groups...</i>",
        parse_mode="HTML",
    )

    # Run auto-discovery in background task
    async def run_discovery_bg():
        try:
            from auto_discover import TelegramGroupDiscoverer
            discoverer = TelegramGroupDiscoverer()
            await discoverer.start()
            res = await discoverer.discover_and_index(
                keywords=[query_term],
                category_slug=category_term,
                max_groups=3,
                members_per_group=100,
                export_to_file=True,
            )
            await discoverer.stop()

            summary = (
                f"✅ <b>Auto-Discovery & Scan Complete!</b>\n\n"
                f"• <b>Keyword:</b> <code>{query_term}</code>\n"
                f"• <b>Open Groups Found:</b> {res.get('discovered_groups_count', 0)}\n"
                f"• <b>Groups Crawled:</b> {res.get('crawled_groups_count', 0)}\n"
                f"• <b>New Members Indexed:</b> <b>+{res.get('total_members_indexed', 0)}</b>\n\n"
                f"Use <code>/search {query_term}</code> or browse categories to view results!"
            )
            await status_msg.edit_text(summary, parse_mode="HTML")
        except Exception as e:
            await status_msg.edit_text(f"❌ Error during auto-discovery: {str(e)}")

    asyncio.create_task(run_discovery_bg())


# ---------------- Inline Query Mode (Search directory from any chat) ----------------

@dp.inline_query()
async def inline_search(inline_query: InlineQuery):
    query = inline_query.query.strip()
    results, _ = await search_directory(query=query if query else None, page=1, page_size=10)

    articles = []
    for m in results:
        username = m["username"]
        name = f"{m['first_name']} {m['last_name']}".strip() or username
        categories = ", ".join(m["categories"])

        text_content = (
            f"👤 <b>{name}</b> (@{username})\n"
            f"🏷️ <b>Categories:</b> {categories}\n"
            f"🔗 <a href=\"https://t.me/{username}\">t.me/{username}</a>"
        )

        articles.append(
            InlineQueryResultArticle(
                id=str(m["id"]),
                title=f"@{username} ({name})",
                description=f"Categories: {categories} | Status: {m.get('last_seen', 'unknown')}",
                input_message_content=InputTextMessageContent(
                    message_text=text_content,
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                ),
            )
        )

    await inline_query.answer(articles, cache_time=10, is_personal=True)


# ---------------- Entrypoint ----------------

async def main():
    if not settings.BOT_TOKEN:
        logger.error("BOT_TOKEN is not configured! Please set it in .env")
        return

    await init_db()
    await seed_default_categories()

    # Start Uptime HTTP Server & Self-Ping loop to prevent sleep on Render
    if settings.ENABLE_WEB_SERVER:
        try:
            from uptime_server import start_uptime_web_server
            await start_uptime_web_server(port=settings.PORT)
        except Exception as e:
            logger.warning(f"Could not start uptime web server: {e}")

    bot = Bot(token=settings.BOT_TOKEN)
    logger.info("Bot started and polling for search queries...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
