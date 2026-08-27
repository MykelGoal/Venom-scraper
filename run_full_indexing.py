import asyncio
import logging
import random
from auto_discover import DeepTelegramDiscoverer
from seed_manager import export_current_to_seed
from export_members import export_members
from database import get_directory_stats, get_all_categories

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("FullHarvest")

NICHES = [
    {
        "category": "betting",
        "category_name": "Betting & Sports",
        "queries": ["sportybet group", "sports betting chat", "betting tips"],
        "max_groups": 3,
        "limit": 300,
    },
    {
        "category": "crypto",
        "category_name": "Crypto & Web3",
        "queries": ["binance api", "crypto trading chat", "defi community"],
        "max_groups": 3,
        "limit": 300,
    },
    {
        "category": "tech",
        "category_name": "Tech & Programming",
        "queries": ["django chat", "flutter chat", "python programmers"],
        "max_groups": 3,
        "limit": 300,
    },
    {
        "category": "finance",
        "category_name": "Finance & Trading",
        "queries": ["forex signals chat", "forex traders community"],
        "max_groups": 2,
        "limit": 250,
    },
    {
        "category": "gaming",
        "category_name": "Gaming & Esports",
        "queries": ["gaming community chat", "esports gamers"],
        "max_groups": 2,
        "limit": 250,
    },
]

async def run_master_pipeline():
    logger.info("=" * 60)
    logger.info("🚀 STARTING AUTOMATED MULTI-NICHE HARVEST & SEED PIPELINE")
    logger.info("=" * 60)

    discoverer = DeepTelegramDiscoverer()
    await discoverer.start()

    try:
        for idx, niche in enumerate(NICHES, start=1):
            cat = niche["category"]
            cat_name = niche["category_name"]
            queries = niche["queries"]
            max_g = niche["max_groups"]
            lim = niche["limit"]

            logger.info(f"\n[{idx}/{len(NICHES)}] Scanning Niche: '{cat_name}' (Queries: {queries})...")

            res = await discoverer.execute_deep_scan(
                keywords=queries,
                category_slug=cat,
                category_name=cat_name,
                max_groups=max_g,
                members_per_group=lim,
                export_to_file=False,
            )

            logger.info(f"Niche '{cat_name}' complete: Found {res.get('discovered_open_groups', 0)} groups, indexed +{res.get('total_members_indexed', 0)} members.")

            # Pause between niches
            pause = random.uniform(15.0, 25.0)
            logger.info(f"Resting for {pause:.1f}s before next niche...")
            await asyncio.sleep(pause)

    finally:
        await discoverer.stop()

    # Export bundled seed dataset
    logger.info("\nBundling all indexed data into initial_seed.json...")
    await export_current_to_seed()

    # Export master CSV and TXT
    await export_members(output_format="csv", filename="master_directory.csv")
    await export_members(output_format="txt", filename="master_directory.txt")

    stats = await get_directory_stats()
    cats = await get_all_categories()

    print("\n" + "=" * 60)
    print("🎉 FULL HARVEST PIPELINE COMPLETE")
    print("=" * 60)
    print(f"Total Members Indexed  : {stats['total_members']:,}")
    print(f"Total Groups Scanned   : {stats['total_groups']:,}")
    print(f"Total Categories       : {stats['total_categories']:,}")
    print("=" * 60)
    for c in cats:
        print(f" • {c['name']}: {c['member_count']} members")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_master_pipeline())
