import asyncio
import logging
import os
import random
from telethon import TelegramClient, functions, errors
from config import settings
from database import init_db, seed_default_categories, get_or_create_category, upsert_group, bulk_save_members, get_directory_stats, get_all_categories
from indexer import TelegramIndexer
from export_members import export_members
from seed_manager import export_current_to_seed

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("MultiNicheHarvest")

TARGET_NICHES = [
    {
        "category_slug": "crypto",
        "category_name": "Crypto & Web3",
        "search_terms": ["binance api", "crypto trading chat", "crypto signals global"],
    },
    {
        "category_slug": "betting",
        "category_name": "Betting & Sports",
        "search_terms": ["sportybet group", "sports betting chat", "sure odds betting"],
    },
    {
        "category_slug": "tech",
        "category_name": "Tech & Programming",
        "search_terms": ["django chat", "flutter chat", "python programmers", "javascript developers"],
    },
    {
        "category_slug": "finance",
        "category_name": "Finance & Trading",
        "search_terms": ["forex signals chat", "forex traders community", "stock market investing"],
    },
    {
        "category_slug": "gaming",
        "category_name": "Gaming & Esports",
        "search_terms": ["gaming community chat", "esports gamers community", "pc gamers chat"],
    },
    {
        "category_slug": "marketing",
        "category_name": "E-Commerce & Marketing",
        "search_terms": ["dropshipping community", "affiliate marketing hub", "ecommerce growth"],
    },
]

async def harvest_all():
    await init_db()
    await seed_default_categories()
    os.makedirs("exports", exist_ok=True)

    client = TelegramClient(settings.SESSION_NAME, settings.API_ID, settings.API_HASH)
    await client.start(phone=settings.PHONE_NUMBER)

    indexer = TelegramIndexer(session_name=settings.SESSION_NAME)
    indexer.client = client

    logger.info("=" * 65)
    logger.info("🚀 STARTING MULTI-NICHE GLOBAL TELEGRAM HARVEST")
    logger.info("=" * 65)

    for idx, niche in enumerate(TARGET_NICHES, start=1):
        slug = niche["category_slug"]
        cat_name = niche["category_name"]
        terms = niche["search_terms"]

        logger.info(f"\n[{idx}/{len(TARGET_NICHES)}] 🔍 Searching Niche: {cat_name.upper()}...")

        discovered_open_groups = []
        for term in terms:
            if len(discovered_open_groups) >= 3:
                break
            try:
                res = await client(functions.contacts.SearchRequest(q=term, limit=8))
                for chat in res.chats:
                    u = getattr(chat, "username", None)
                    t = getattr(chat, "title", "Untitled")
                    if u and not any(g["username"].lower() == u.lower() for g in discovered_open_groups):
                        try:
                            # Test if readable
                            count = 0
                            async for _ in client.iter_participants(chat, limit=1):
                                count += 1
                                break
                            if count > 0:
                                logger.info(f"  ✨ Found open group in {slug}: @{u} ('{t}')")
                                discovered_open_groups.append({"username": u, "title": t})
                                if len(discovered_open_groups) >= 3:
                                    break
                        except Exception:
                            pass
            except Exception as e:
                logger.debug(f"Search query error: {e}")
            await asyncio.sleep(random.uniform(1.0, 2.0))

        logger.info(f"Found {len(discovered_open_groups)} open groups for {cat_name}. Crawling members...")

        for g in discovered_open_groups:
            u = g["username"]
            logger.info(f"  ➡️ Crawling @{u}...")
            try:
                res = await indexer.index_public_group(
                    group_identifier=u,
                    category_slug=slug,
                    category_name=cat_name,
                    max_members=150,
                )
                logger.info(f"  ✅ @{u}: Indexed {res.get('indexed_members', 0)} members.")
            except Exception as e:
                logger.warning(f"Failed to crawl @{u}: {e}")
            await asyncio.sleep(random.uniform(3.0, 6.0))

        # Export this category's file
        try:
            await export_members(output_format="csv", category_slug=slug, filename=f"exports/{slug}_members.csv")
            await export_members(output_format="txt", category_slug=slug, filename=f"exports/{slug}_usernames.txt")
        except Exception as e:
            logger.debug(f"Export notice for {slug}: {e}")

        # Pause between categories
        await asyncio.sleep(random.uniform(8.0, 15.0))

    await client.disconnect()

    # Export master files
    logger.info("\nExporting master files...")
    await export_members(output_format="csv", filename="exports/all_members.csv")
    await export_members(output_format="txt", filename="exports/all_usernames.txt")
    await export_current_to_seed()

    stats = await get_directory_stats()
    cats = await get_all_categories()

    print("\n" + "=" * 65)
    print("🎉 MULTI-NICHE HARVEST SUMMARY")
    print("=" * 65)
    print(f"Total Unique Members Indexed : {stats['total_members']:,}")
    print(f"Total Public Groups Scanned  : {stats['total_groups']:,}")
    print(f"Total Categories Populated   : {stats['total_categories']:,}")
    print("=" * 65)
    for c in cats:
        print(f" • {c['name']:<25}: {c['member_count']:,} members")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(harvest_all())
