import asyncio
import logging
import random
from typing import List, Optional

from telethon import TelegramClient, errors
from telethon.tl.types import (
    Channel,
    Chat,
    User,
    UserStatusRecently,
    UserStatusOnline,
    UserStatusLastWeek,
    UserStatusLastMonth,
    UserStatusOffline,
)

from config import settings
from database import (
    AsyncSessionLocal,
    bulk_save_members,
    get_or_create_category,
    init_db,
    seed_default_categories,
    upsert_group,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("TG_Indexer")


def parse_user_status(status) -> str:
    """Classifies user activity status to distinguish active vs dormant users."""
    if isinstance(status, UserStatusOnline):
        return "online"
    elif isinstance(status, UserStatusRecently):
        return "recently"
    elif isinstance(status, UserStatusLastWeek):
        return "within_week"
    elif isinstance(status, UserStatusLastMonth):
        return "within_month"
    elif isinstance(status, UserStatusOffline):
        return "offline"
    return "unknown"


class TelegramIndexer:
    def __init__(self, session_name: str = settings.SESSION_NAME):
        self.session_name = session_name
        from telethon.sessions import StringSession
        if settings.TELEGRAM_STRING_SESSION:
            sess = StringSession(settings.TELEGRAM_STRING_SESSION)
        else:
            sess = self.session_name

        self.client = TelegramClient(
            sess,
            settings.API_ID,
            settings.API_HASH,
        )

    async def start(self):
        logger.info("Connecting Telethon client...")
        if settings.TELEGRAM_STRING_SESSION:
            await self.client.start()
        else:
            await self.client.start(phone=settings.PHONE_NUMBER)
        me = await self.client.get_me()
        logger.info(f"Authenticated as @{me.username or me.id} ({me.first_name})")

    async def stop(self):
        await self.client.disconnect()
        logger.info("Telethon client disconnected.")

    async def _safe_delay(self):
        """Applies jittered delay to mimic natural browsing and prevent MTProto flood flags."""
        delay = random.uniform(settings.REQUEST_DELAY_MIN, settings.REQUEST_DELAY_MAX)
        logger.debug(f"Sleeping for {delay:.2f}s...")
        await asyncio.sleep(delay)

    async def index_public_group(
        self,
        group_identifier: str,
        category_slug: str,
        category_name: Optional[str] = None,
        max_members: int = settings.MAX_MEMBERS_PER_GROUP,
    ) -> dict:
        """
        Scans a public Telegram group/channel and indexes members with public usernames.
        group_identifier: '@username' or 'https://t.me/username' or username string
        """
        clean_target = group_identifier.replace("https://t.me/", "").replace("t.me/", "").lstrip("@")
        logger.info(f"Starting crawl for group: @{clean_target} [Category: {category_slug}]")

        try:
            entity = await self.client.get_entity(clean_target)
        except errors.FloodWaitError as e:
            logger.warning(f"FloodWait hit on get_entity: sleeping for {e.seconds}s")
            await asyncio.sleep(e.seconds + 2)
            entity = await self.client.get_entity(clean_target)
        except Exception as e:
            logger.error(f"Failed to resolve group @{clean_target}: {e}")
            return {"status": "error", "message": f"Cannot find group: {str(e)}"}

        if not isinstance(entity, (Channel, Chat)):
            logger.warning(f"Target @{clean_target} is not a valid group or supergroup.")
            return {"status": "error", "message": "Target is not a group/channel."}

        # Check if participants list is accessible
        total_participants = getattr(entity, "participants_count", 0) or 0
        group_title = getattr(entity, "title", clean_target)
        group_tg_id = entity.id

        # Upsert Category & Group in DB
        async with AsyncSessionLocal() as session:
            category = await get_or_create_category(
                session=session,
                name=category_name or category_slug.capitalize(),
                slug=category_slug.lower(),
            )
            group = await upsert_group(
                session=session,
                telegram_id=group_tg_id,
                title=group_title,
                username=getattr(entity, "username", clean_target),
                category_id=category.id,
                member_count=total_participants,
            )
            group_db_id = group.id
            await session.commit()

        logger.info(f"Registered group in DB: '{group_title}' (ID: {group_db_id}). Starting member iteration...")

        scanned_count = 0
        indexed_count = 0
        filtered_out_bots = 0
        filtered_out_no_user = 0
        batch = []
        batch_size = 100

        try:
            # Participant extraction logic:
            # 1. Basic crawl (< 200)
            # 2. 1-character search (200 - 2,000)
            # 3. 2-character combinatorial search (> 2,000) for massive 10k-50k member extractions
            search_filters = [""]
            if max_members > 2000:
                # 2-character combinatorial expansion (aa..zz, a0..z9, etc.)
                chars = [chr(c) for c in range(ord('a'), ord('z') + 1)] + [str(d) for d in range(10)]
                search_filters = [f"{c1}{c2}" for c1 in chars for c2 in chars]
            elif max_members > 200:
                # 1-character alphanumeric search (a-z, 0-9, _)
                search_filters = [chr(c) for c in range(ord('a'), ord('z') + 1)] + [str(d) for d in range(10)] + ["_"]

            seen_user_ids = set()

            for s_filter in search_filters:
                if scanned_count >= max_members or indexed_count >= max_members:
                    break

                try:
                    async for user in self.client.iter_participants(entity, search=s_filter if s_filter else None, limit=200):
                        if scanned_count >= max_members or indexed_count >= max_members:
                            break

                        if user.id in seen_user_ids:
                            continue
                        seen_user_ids.add(user.id)
                        scanned_count += 1

                        # Filter 1: Ignore non-users, bots, deleted accounts
                        if not isinstance(user, User) or user.bot or user.deleted:
                            filtered_out_bots += 1
                            continue

                        # Filter 2: Only users with a publicly set username
                        if not user.username:
                            filtered_out_no_user += 1
                            continue

                        member_record = {
                            "telegram_id": user.id,
                            "username": user.username,
                            "raw_username": user.username,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                            "last_seen_status": parse_user_status(user.status),
                        }
                        batch.append(member_record)

                        # Batch save to database in chunks of 100
                        if len(batch) >= batch_size:
                            async with AsyncSessionLocal() as session:
                                new_saved, _ = await bulk_save_members(session, group_db_id, batch)
                                indexed_count += len(batch)
                                if indexed_count % 500 == 0 or indexed_count <= 200:
                                    logger.info(f"[@{clean_target}] Deep indexed {indexed_count:,} valid members (+{new_saved} new)...")
                            batch.clear()
                            await self._safe_delay()

                except errors.FloodWaitError as e:
                    logger.warning(f"FloodWait on search filter '{s_filter}': sleeping for {e.seconds}s")
                    await asyncio.sleep(e.seconds + 2)
                except Exception as e:
                    logger.debug(f"Filter '{s_filter}' error on @{clean_target}: {e}")

            # Process remaining batch items
            if batch:
                async with AsyncSessionLocal() as session:
                    await bulk_save_members(session, group_db_id, batch)
                    indexed_count += len(batch)
                batch.clear()

            logger.info(
                f"Finished crawl for @{clean_target}: {scanned_count} scanned, {indexed_count} indexed, "
                f"{filtered_out_no_user} without username, {filtered_out_bots} bots/deleted ignored."
            )

            return {
                "status": "success",
                "group_title": group_title,
                "scanned_total": scanned_count,
                "indexed_members": indexed_count,
                "skipped_no_username": filtered_out_no_user,
                "skipped_bots": filtered_out_bots,
            }

        except errors.FloodWaitError as e:
            logger.error(f"Telegram FloodWait reached: Must pause for {e.seconds}s.")
            await asyncio.sleep(e.seconds + 5)
            return {"status": "partial", "error": f"FloodWait of {e.seconds}s occurred."}
        except errors.ChatAdminRequiredError:
            logger.error(f"Cannot read participant list in @{clean_target}: member list is hidden or restricted.")
            return {"status": "error", "message": "Group member list is hidden by group admins."}
        except Exception as e:
            logger.exception(f"Unexpected error while indexing @{clean_target}: {e}")
            return {"status": "error", "message": str(e)}


# ---------------- CLI / Standalone Runner ----------------

async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Telegram Public Group Member Indexer")
    parser.add_argument("--group", type=str, help="Telegram group username (e.g. binance_announcements or web3devs)")
    parser.add_argument("--category", type=str, default="tech", help="Category slug (e.g. crypto, gaming, tech, betting)")
    parser.add_argument("--category-name", type=str, default=None, help="Display name for the category")
    parser.add_argument("--limit", type=int, default=1000, help="Max members to scan per group")
    args = parser.parse_args()

    await init_db()
    await seed_default_categories()

    if not args.group:
        print("Usage: python indexer.py --group <group_username> --category <category_slug>")
        print("Example: python indexer.py --group eth_developers --category crypto --limit 500")
        return

    indexer = TelegramIndexer()
    await indexer.start()
    try:
        res = await indexer.index_public_group(
            group_identifier=args.group,
            category_slug=args.category,
            category_name=args.category_name,
            max_members=args.limit,
        )
        print("\n=== Indexing Summary ===")
        for k, v in res.items():
            print(f"{k}: {v}")
    finally:
        await indexer.stop()


if __name__ == "__main__":
    asyncio.run(main())
