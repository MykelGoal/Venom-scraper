import asyncio
import logging
import random
from typing import List, Dict, Optional
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
logger = logging.getLogger("AutoDiscover")


class TelegramGroupDiscoverer:
    def __init__(self, session_name: str = settings.SESSION_NAME):
        self.session_name = session_name
        self.client = TelegramClient(self.session_name, settings.API_ID, settings.API_HASH)
        self.indexer = TelegramIndexer(session_name=session_name)

    async def start(self):
        await self.client.start(phone=settings.PHONE_NUMBER)
        # Share client session with indexer
        self.indexer.client = self.client

    async def stop(self):
        await self.client.disconnect()

    async def find_public_groups(self, keyword: str, limit: int = 15) -> List[Dict]:
        """
        Searches Telegram globally for public groups matching a keyword,
        and tests if their participant list is publicly readable.
        """
        logger.info(f"Searching Telegram for public groups matching '{keyword}'...")
        try:
            search_result = await self.client(functions.contacts.SearchRequest(q=keyword, limit=limit))
        except errors.FloodWaitError as e:
            logger.warning(f"FloodWait on search: sleeping {e.seconds}s")
            await asyncio.sleep(e.seconds + 2)
            search_result = await self.client(functions.contacts.SearchRequest(q=keyword, limit=limit))
        except Exception as e:
            logger.error(f"Search request failed: {e}")
            return []

        discovered_groups = []

        for chat in search_result.chats:
            username = getattr(chat, "username", None)
            title = getattr(chat, "title", "Untitled")

            # Must be a channel/supergroup/chat with a public username
            if not isinstance(chat, (Channel, Chat)) or not username:
                continue

            # Test if member list is open and readable
            is_open = False
            total_members = getattr(chat, "participants_count", 0) or 0

            try:
                # Test iteration of 1 participant to verify permissions
                async for _ in self.client.iter_participants(chat, limit=1):
                    is_open = True
                    break
            except (errors.ChatAdminRequiredError, errors.ChannelPrivateError):
                logger.debug(f"Group @{username} ('{title}') has hidden member list. Skipping.")
                is_open = False
            except Exception as e:
                logger.debug(f"Cannot read @{username}: {e}")
                is_open = False

            if is_open:
                logger.info(f"✨ Found open public group: @{username} | '{title}' (~{total_members} members)")
                discovered_groups.append({
                    "username": username,
                    "title": title,
                    "members_count": total_members,
                })
            else:
                logger.debug(f"🔒 Group @{username} is private or has restricted list.")

        logger.info(f"Found {len(discovered_groups)} open public groups for '{keyword}'.")
        return discovered_groups

    async def discover_and_index(
        self,
        keywords: List[str],
        category_slug: str,
        category_name: Optional[str] = None,
        max_groups: int = 3,
        members_per_group: int = 200,
        export_to_file: bool = True,
    ) -> Dict:
        """
        Automatically discovers groups matching keywords, crawls members, and saves everything.
        """
        await init_db()
        await seed_default_categories()

        all_discovered = []
        indexed_groups_summary = []
        total_indexed_all = 0

        for kw in keywords:
            groups = await self.find_public_groups(kw, limit=15)
            for g in groups:
                if not any(d["username"].lower() == g["username"].lower() for d in all_discovered):
                    all_discovered.append(g)

        logger.info(f"\nDiscovered {len(all_discovered)} unique open public groups across keywords: {keywords}")

        # Limit to max_groups
        targets_to_crawl = all_discovered[:max_groups]

        if not targets_to_crawl:
            logger.warning("No open public groups found with readable member lists.")
            return {"status": "no_groups_found", "indexed_members": 0}

        for idx, target in enumerate(targets_to_crawl, start=1):
            username = target["username"]
            logger.info(f"\n[{idx}/{len(targets_to_crawl)}] Auto-indexing @{username} ('{target['title']}')...")

            res = await self.indexer.index_public_group(
                group_identifier=username,
                category_slug=category_slug,
                category_name=category_name,
                max_members=members_per_group,
            )

            indexed_count = res.get("indexed_members", 0)
            total_indexed_all += indexed_count
            indexed_groups_summary.append({
                "group": f"@{username}",
                "title": target["title"],
                "indexed": indexed_count,
            })

            # Rest delay between groups
            if idx < len(targets_to_crawl):
                pause = random.uniform(settings.BATCH_PAUSE_SECONDS, settings.BATCH_PAUSE_SECONDS + 10)
                logger.info(f"Resting {pause:.1f}s before indexing next discovered group...")
                await asyncio.sleep(pause)

        exported_filename = None
        if export_to_file and total_indexed_all > 0:
            exported_filename = await export_members(
                output_format="csv",
                category_slug=category_slug,
                filename=f"discovered_{category_slug}_members.csv",
            )
            await export_members(
                output_format="txt",
                category_slug=category_slug,
                filename=f"discovered_{category_slug}_usernames.txt",
            )

        return {
            "status": "success",
            "discovered_groups_count": len(all_discovered),
            "crawled_groups_count": len(targets_to_crawl),
            "total_members_indexed": total_indexed_all,
            "groups_summary": indexed_groups_summary,
            "exported_file": exported_filename,
        }


# ---------------- CLI Runner ----------------

async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Auto-Discover and Index Public Telegram Groups by Keyword")
    parser.add_argument("--query", "-q", type=str, required=True, help="Search keyword (e.g. 'sportybet', 'crypto trading', 'web3')")
    parser.add_argument("--category", "-c", type=str, default="betting", help="Category slug (crypto, betting, tech, gaming, finance, marketing)")
    parser.add_argument("--category-name", type=str, default=None, help="Display name for category")
    parser.add_argument("--max-groups", type=int, default=3, help="Max open groups to crawl (default: 3)")
    parser.add_argument("--limit", type=int, default=150, help="Max members per group (default: 150)")
    parser.add_argument("--no-export", action="store_true", help="Do not export CSV/TXT files after indexing")

    args = parser.parse_args()

    discoverer = TelegramGroupDiscoverer()
    await discoverer.start()

    try:
        keywords = [k.strip() for k in args.query.split(",") if k.strip()]
        result = await discoverer.discover_and_index(
            keywords=keywords,
            category_slug=args.category,
            category_name=args.category_name,
            max_groups=args.max_groups,
            members_per_group=args.limit,
            export_to_file=not args.no_export,
        )

        print("\n" + "=" * 60)
        print("🎉 AUTO-DISCOVERY & INDEXING SUMMARY")
        print("=" * 60)
        print(f"Keywords Searched     : {args.query}")
        print(f"Category Assigned     : {args.category}")
        print(f"Open Groups Found     : {result.get('discovered_groups_count', 0)}")
        print(f"Groups Crawled        : {result.get('crawled_groups_count', 0)}")
        print(f"Total Members Indexed : {result.get('total_members_indexed', 0)}")
        if result.get("exported_file"):
            print(f"Exported CSV File     : {result.get('exported_file')}")
        print("=" * 60)
        for g in result.get("groups_summary", []):
            print(f" - {g['group']} ({g['title']}): {g['indexed']} members")
        print("=" * 60)

    finally:
        await discoverer.stop()


if __name__ == "__main__":
    asyncio.run(main())
