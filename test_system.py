import asyncio
import os
import unittest

from database import (
    init_db,
    seed_default_categories,
    upsert_group,
    bulk_save_members,
    search_directory,
    get_all_categories,
    get_directory_stats,
    AsyncSessionLocal,
    get_or_create_category,
)

class TestDirectoryDatabase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Drop and recreate tables for clean testing state
        from database import engine, Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        await seed_default_categories()

    async def test_indexing_and_searching(self):
        async with AsyncSessionLocal() as session:
            cat = await get_or_create_category(session, "Crypto & Web3", "crypto")
            group = await upsert_group(
                session=session,
                telegram_id=987654321,
                title="Ethereum Developers",
                username="eth_devs",
                category_id=cat.id,
                member_count=1500,
            )
            group_id = group.id
            await session.commit()

        # Mock sample members
        sample_members = [
            {
                "telegram_id": 1001,
                "username": "satoshi_nakamoto",
                "raw_username": "satoshi_nakamoto",
                "first_name": "Satoshi",
                "last_name": "Nakamoto",
                "last_seen_status": "recently",
            },
            {
                "telegram_id": 1002,
                "username": "vitalik_fan",
                "raw_username": "Vitalik_Fan",
                "first_name": "Vitalik",
                "last_name": "Fan",
                "last_seen_status": "online",
            },
            {
                "telegram_id": 1003,
                "username": "crypto_trader_99",
                "raw_username": "crypto_trader_99",
                "first_name": "Crypto",
                "last_name": "Trader",
                "last_seen_status": "within_week",
            },
        ]

        async with AsyncSessionLocal() as session:
            new_cnt, assoc_cnt = await bulk_save_members(session, group_id, sample_members)
            self.assertEqual(new_cnt, 3)
            self.assertEqual(assoc_cnt, 3)

        # 1. Test search by keyword
        results, total = await search_directory(query="satoshi")
        self.assertEqual(total, 1)
        self.assertEqual(results[0]["username"], "satoshi_nakamoto")
        self.assertIn("Crypto & Web3", results[0]["categories"])

        # 2. Test search by category
        results, total = await search_directory(category_slug="crypto")
        self.assertEqual(total, 3)

        # 3. Test stats
        stats = await get_directory_stats()
        self.assertGreaterEqual(stats["total_members"], 3)
        self.assertGreaterEqual(stats["total_groups"], 1)

        # 4. Test categories list
        cats = await get_all_categories()
        crypto_cat = next((c for c in cats if c["slug"] == "crypto"), None)
        self.assertIsNotNone(crypto_cat)
        self.assertGreaterEqual(crypto_cat["member_count"], 3)
        print("\nAll database & search pipeline tests passed successfully!")

if __name__ == "__main__":
    unittest.main()
