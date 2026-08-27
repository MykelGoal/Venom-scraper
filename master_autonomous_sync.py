import asyncio
import logging
import os
import random
from typing import Dict, List
from auto_discover import DeepTelegramDiscoverer
from database import init_db, seed_default_categories, get_directory_stats, get_all_categories
from export_members import export_members
from seed_manager import export_current_to_seed

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("AutonomousSync")

# Comprehensive Master Taxonomy of Telegram Niches & Search Queries
MASTER_DIRECTORY_CATALOG = [
    {
        "category_slug": "crypto",
        "category_name": "Crypto & Web3",
        "keywords": [
            "crypto trading", "binance", "solana", "ethereum", "bitcoin",
            "defi", "airdrop", "memecoin", "bybit", "crypto signals"
        ],
        "max_groups": 4,
        "limit_per_group": 250,
    },
    {
        "category_slug": "betting",
        "category_name": "Betting & Sports",
        "keywords": [
            "sportybet", "sports betting", "bet9ja", "1xbet", "fixed matches",
            "betting tips", "sure odds", "football betting", "stake betting"
        ],
        "max_groups": 4,
        "limit_per_group": 250,
    },
    {
        "category_slug": "finance",
        "category_name": "Finance & Trading",
        "keywords": [
            "forex signals", "forex traders", "deriv", "stock market",
            "binary options", "forex academy", "day trading", "investing"
        ],
        "max_groups": 3,
        "limit_per_group": 200,
    },
    {
        "category_slug": "tech",
        "category_name": "Tech & Programming",
        "keywords": [
            "python developers", "django developers", "flutter programmers",
            "javascript coders", "react native", "ai developers", "web developers"
        ],
        "max_groups": 3,
        "limit_per_group": 200,
    },
    {
        "category_slug": "gaming",
        "category_name": "Gaming & Esports",
        "keywords": [
            "gaming community", "esports gamers", "pubg mobile chat",
            "cod mobile", "free fire", "dota 2 chat", "pc gamers"
        ],
        "max_groups": 3,
        "limit_per_group": 200,
    },
    {
        "category_slug": "marketing",
        "category_name": "E-Commerce & Marketing",
        "keywords": [
            "dropshipping", "affiliate marketing", "digital marketing",
            "ecommerce growth", "shopify store", "social media marketing"
        ],
        "max_groups": 3,
        "limit_per_group": 200,
    },
]


async def run_autonomous_sweep(loop_forever: bool = False, loop_delay_hours: int = 6):
    """
    Autonomously scans all niches across Telegram, extracts members,
    saves to database, exports individual category files, and bundles seeds.
    """
    await init_db()
    await seed_default_categories()

    os.makedirs("exports", exist_ok=True)

    discoverer = DeepTelegramDiscoverer()
    await discoverer.start()

    try:
        while True:
            logger.info("=" * 65)
            logger.info("🌐 STARTING FULL AUTONOMOUS TELEGRAM DIRECTORY HARVEST")
            logger.info("=" * 65)

            for idx, niche in enumerate(MASTER_DIRECTORY_CATALOG, start=1):
                slug = niche["category_slug"]
                name = niche["category_name"]
                kws = niche["keywords"]
                max_g = niche["max_groups"]
                limit = niche["limit_per_group"]

                logger.info(f"\n=======================================================")
                logger.info(f"[{idx}/{len(MASTER_DIRECTORY_CATALOG)}] Processing Niche: {name.upper()}")
                logger.info(f"Keywords: {', '.join(kws)}")
                logger.info(f"=======================================================")

                try:
                    res = await discoverer.execute_deep_scan(
                        keywords=kws,
                        category_slug=slug,
                        category_name=name,
                        max_groups=max_g,
                        members_per_group=limit,
                        export_to_file=False,
                    )
                    logger.info(f"✨ Niche '{name}' Complete: Indexed +{res.get('total_members_indexed', 0)} members.")
                except Exception as e:
                    logger.error(f"Error scanning niche '{name}': {e}")

                # Export individual niche files
                try:
                    await export_members(
                        output_format="csv",
                        category_slug=slug,
                        filename=f"exports/{slug}_members.csv"
                    )
                    await export_members(
                        output_format="txt",
                        category_slug=slug,
                        filename=f"exports/{slug}_usernames.txt"
                    )
                except Exception as e:
                    logger.debug(f"Export notice for {slug}: {e}")

                # Rest between niches to avoid MTProto limits
                pause = random.uniform(20.0, 35.0)
                logger.info(f"Cooling down for {pause:.1f}s before moving to next niche...")
                await asyncio.sleep(pause)

            # Export Master Unified Dataset
            logger.info("\nExporting Master Unified Datasets & Bundling Seed...")
            await export_members(output_format="csv", filename="exports/all_members.csv")
            await export_members(output_format="txt", filename="exports/all_usernames.txt")
            await export_current_to_seed()

            stats = await get_directory_stats()
            cats = await get_all_categories()

            logger.info("\n" + "=" * 65)
            logger.info("🎉 AUTONOMOUS HARVEST COMPLETE — DIRECTORY STATUS")
            logger.info("=" * 65)
            logger.info(f"Total Active Members Indexed : {stats['total_members']:,}")
            logger.info(f"Total Public Groups Scanned  : {stats['total_groups']:,}")
            logger.info(f"Active Directory Categories  : {stats['total_categories']:,}")
            for c in cats:
                logger.info(f" • {c['name']:<25}: {c['member_count']:,} members")
            logger.info("=" * 65)

            if not loop_forever:
                break

            logger.info(f"\nNext automated sweep scheduled in {loop_delay_hours} hours...")
            await asyncio.sleep(loop_delay_hours * 3600)

    finally:
        await discoverer.stop()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Autonomous Full-Directory Harvester & Sync Engine")
    parser.add_argument("--loop", action="store_true", help="Run continuously on a schedule (e.g. every 6 hours)")
    parser.add_argument("--interval", type=int, default=6, help="Hours between sweeps if --loop is enabled")
    args = parser.parse_args()

    asyncio.run(run_autonomous_sweep(loop_forever=args.loop, loop_delay_hours=args.interval))
