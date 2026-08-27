import asyncio
import json
import logging
import os
import random

from config import settings
from database import init_db, seed_default_categories
from indexer import TelegramIndexer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("BatchIndexer")


async def run_batch(file_path: str = "groups.json"):
    if not os.path.exists(file_path):
        logger.error(f"Target list file '{file_path}' not found! Create it or copy from groups.example.json.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        groups_to_index = json.load(f)

    logger.info(f"Loaded {len(groups_to_index)} target groups from {file_path}.")

    await init_db()
    await seed_default_categories()

    indexer = TelegramIndexer()
    await indexer.start()

    try:
        for idx, item in enumerate(groups_to_index, start=1):
            username = item.get("username")
            category = item.get("category", "tech")
            category_name = item.get("category_name")
            limit = item.get("limit", settings.MAX_MEMBERS_PER_GROUP)

            logger.info(f"\n--- [{idx}/{len(groups_to_index)}] Indexing @{username} (Niche: {category}) ---")
            
            result = await indexer.index_public_group(
                group_identifier=username,
                category_slug=category,
                category_name=category_name,
                max_members=limit,
            )
            logger.info(f"Group @{username} result: {result.get('status')} | Indexed: {result.get('indexed_members', 0)}")

            # Pause between groups to prevent Telegram heuristics from flagging the account
            inter_group_delay = random.uniform(settings.BATCH_PAUSE_SECONDS, settings.BATCH_PAUSE_SECONDS + 15)
            logger.info(f"Resting for {inter_group_delay:.1f}s before next group...")
            await asyncio.sleep(inter_group_delay)

    finally:
        await indexer.stop()
        logger.info("Batch indexing completed.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, default="groups.example.json", help="Path to JSON file with groups list")
    args = parser.parse_args()
    asyncio.run(run_batch(args.file))
