import asyncio
import logging
import random
import re
from typing import List, Dict, Optional, Set
from telethon import TelegramClient, functions, errors
from telethon.tl.types import Channel, Chat, User

from config import settings
from database import init_db, seed_default_categories
from indexer import TelegramIndexer
from export_members import export_members

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("DeepDiscovery")


def generate_search_permutations(base_query: str) -> List[str]:
    """Expands a single keyword into a rich set of discovery queries."""
    clean = base_query.strip().lower()
    suffixes = [
        "",
        "group",
        "chat",
        "community",
        "discussion",
        "official",
        "tips",
        "hub",
        "club",
        "global",
        "nigeria",
        "africa",
        "vip",
        "daily",
        "updates",
        "channel",
        "odds",
        "signals",
    ]
    
    queries = []
    for s in suffixes:
        q = f"{clean} {s}".strip() if s else clean
        if q not in queries:
            queries.append(q)
    return queries


class DeepTelegramDiscoverer:
    def __init__(self, session_name: str = settings.SESSION_NAME):
        self.session_name = session_name
        self.client = TelegramClient(self.session_name, settings.API_ID, settings.API_HASH)
        self.indexer = TelegramIndexer(session_name=session_name)

    async def start(self):
        await self.client.start(phone=settings.PHONE_NUMBER)
        self.indexer.client = self.client

    async def stop(self):
        await self.client.disconnect()

    async def _test_and_filter_group(self, entity) -> Optional[Dict]:
        """Validates if an entity is an open group with readable member lists."""
        username = getattr(entity, "username", None)
        title = getattr(entity, "title", "Untitled")

        if not isinstance(entity, (Channel, Chat)) or not username:
            return None

        total_members = getattr(entity, "participants_count", 0) or 0
        try:
            # Test if at least 1 member can be retrieved
            async for _ in self.client.iter_participants(entity, limit=1):
                logger.info(f"  ✨ [OPEN] @{username} | '{title}' (~{total_members} members)")
                return {
                    "username": username,
                    "title": title,
                    "members_count": total_members,
                }
        except (errors.ChatAdminRequiredError, errors.ChannelPrivateError):
            logger.debug(f"  🔒 [HIDDEN] @{username} ('{title}')")
            return None
        except Exception as e:
            logger.debug(f"  ❌ Error checking @{username}: {e}")
            return None

    async def deep_search_groups(self, keywords: List[str], max_open_groups: int = 10) -> List[Dict]:
        """
        Executes multi-stage deep search:
        1. Global Contacts / Chat Search across all keyword permutations
        2. Global Message Search for public t.me invite links
        """
        discovered_map: Dict[str, Dict] = {}

        # 1. Expand keywords
        all_queries = []
        for kw in keywords:
            all_queries.extend(generate_search_permutations(kw))

        logger.info(f"Initiating Deep Discovery across {len(all_queries)} query permutations...")

        for idx, query in enumerate(all_queries, start=1):
            if len(discovered_map) >= max_open_groups:
                logger.info(f"Target of {max_open_groups} open groups reached.")
                break

            logger.info(f"[{idx}/{len(all_queries)}] Searching query: '{query}'...")
            try:
                res = await self.client(functions.contacts.SearchRequest(q=query, limit=15))
                for chat in res.chats:
                    u = getattr(chat, "username", None)
                    if u and u.lower() not in discovered_map:
                        checked = await self._test_and_filter_group(chat)
                        if checked:
                            discovered_map[u.lower()] = checked
            except errors.FloodWaitError as e:
                logger.warning(f"FloodWait on search query '{query}': sleeping {e.seconds}s")
                await asyncio.sleep(e.seconds + 2)
            except Exception as e:
                logger.debug(f"Search failed for '{query}': {e}")

            # Safe delay between search queries
            await asyncio.sleep(random.uniform(1.0, 2.5))

        logger.info(f"Deep Search completed. Total open readable groups found: {len(discovered_map)}")
        return list(discovered_map.values())

    async def execute_deep_scan(
        self,
        keywords: List[str],
        category_slug: str,
        category_name: Optional[str] = None,
        max_groups: int = 5,
        members_per_group: int = 500,
        export_to_file: bool = True,
    ) -> Dict:
        """
        Performs full deep discovery + deep alphanumeric participant crawling.
        """
        await init_db()
        await seed_default_categories()

        open_groups = await self.deep_search_groups(keywords, max_open_groups=max_groups)

        if not open_groups:
            logger.warning("No open public groups found with readable member lists.")
            return {"status": "no_groups_found", "total_members_indexed": 0}

        targets = open_groups[:max_groups]
        total_indexed = 0
        groups_summary = []

        logger.info(f"\nStarting deep crawl for {len(targets)} targets (Target cap: {members_per_group} members/group)...")

        for idx, target in enumerate(targets, start=1):
            u = target["username"]
            logger.info(f"\n--- [{idx}/{len(targets)}] Deep Crawling @{u} ('{target['title']}') ---")

            res = await self.indexer.index_public_group(
                group_identifier=u,
                category_slug=category_slug,
                category_name=category_name,
                max_members=members_per_group,
            )

            indexed_count = res.get("indexed_members", 0)
            total_indexed += indexed_count
            groups_summary.append({
                "group": f"@{u}",
                "title": target["title"],
                "indexed": indexed_count,
            })

            # Inter-group delay
            if idx < len(targets):
                pause = random.uniform(settings.BATCH_PAUSE_SECONDS, settings.BATCH_PAUSE_SECONDS + 10)
                logger.info(f"Resting {pause:.1f}s before next group crawl...")
                await asyncio.sleep(pause)

        exported_csv = None
        if export_to_file and total_indexed > 0:
            exported_csv = await export_members(
                output_format="csv",
                category_slug=category_slug,
                filename=f"deep_scanned_{category_slug}_members.csv",
            )
            await export_members(
                output_format="txt",
                category_slug=category_slug,
                filename=f"deep_scanned_{category_slug}_usernames.txt",
            )

        return {
            "status": "success",
            "discovered_open_groups": len(open_groups),
            "crawled_groups": len(targets),
            "total_members_indexed": total_indexed,
            "groups_summary": groups_summary,
            "exported_csv": exported_csv,
        }


# ---------------- CLI Runner ----------------

async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Deep Search & Index Public Telegram Groups by Keyword")
    parser.add_argument("--query", "-q", type=str, required=True, help="Search keyword (e.g. 'sportybet', 'crypto', 'forex')")
    parser.add_argument("--category", "-c", type=str, default="betting", help="Category slug (betting, crypto, tech, gaming, finance)")
    parser.add_argument("--category-name", type=str, default=None, help="Display name for category")
    parser.add_argument("--max-groups", type=int, default=15, help="Max open groups to crawl (default: 15)")
    parser.add_argument("--limit", type=int, default=1000, help="Max members to extract per group (e.g., 1000-5000)")
    parser.add_argument("--no-export", action="store_true", help="Disable CSV/TXT file export")

    args = parser.parse_args()

    discoverer = DeepTelegramDiscoverer()
    await discoverer.start()

    try:
        keywords = [k.strip() for k in args.query.split(",") if k.strip()]
        result = await discoverer.execute_deep_scan(
            keywords=keywords,
            category_slug=args.category,
            category_name=args.category_name,
            max_groups=args.max_groups,
            members_per_group=args.limit,
            export_to_file=not args.no_export,
        )

        print("\n" + "=" * 60)
        print("🚀 DEEP DISCOVERY & EXTRACTION COMPLETE")
        print("=" * 60)
        print(f"Keywords Searched     : {args.query}")
        print(f"Category Assigned     : {args.category}")
        print(f"Open Groups Found     : {result.get('discovered_open_groups', 0)}")
        print(f"Groups Crawled        : {result.get('crawled_groups', 0)}")
        print(f"Total Members Indexed : {result.get('total_members_indexed', 0)}")
        if result.get("exported_csv"):
            print(f"Exported CSV File     : {result.get('exported_csv')}")
        print("=" * 60)
        for g in result.get("groups_summary", []):
            print(f" • {g['group']} ({g['title']}): +{g['indexed']} members")
        print("=" * 60)

    finally:
        await discoverer.stop()


if __name__ == "__main__":
    asyncio.run(main())
