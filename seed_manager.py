import asyncio
import os
import json
from sqlalchemy import select, func
from database import (
    AsyncSessionLocal,
    Member,
    TelegramGroup,
    Category,
    MemberGroupAssociation,
    get_or_create_category,
    upsert_group,
    bulk_save_members,
)

INITIAL_DATASET_FILE = "initial_seed.json"

async def export_current_to_seed():
    """Exports current database to a bundled seed JSON file."""
    async with AsyncSessionLocal() as session:
        # Get all groups with category info
        groups_stmt = select(TelegramGroup, Category).join(Category, Category.id == TelegramGroup.category_id)
        groups_res = await session.execute(groups_stmt)
        group_rows = groups_res.all()

        seed_data = []

        for grp, cat in group_rows:
            # Get members for this group
            members_stmt = (
                select(Member)
                .join(MemberGroupAssociation, Member.id == MemberGroupAssociation.member_id)
                .where(MemberGroupAssociation.group_id == grp.id)
            )
            m_res = await session.execute(members_stmt)
            members = m_res.scalars().all()

            seed_data.append({
                "group_title": grp.title,
                "group_username": grp.username,
                "group_telegram_id": grp.telegram_id,
                "category_name": cat.name,
                "category_slug": cat.slug,
                "members": [
                    {
                        "telegram_id": m.telegram_id,
                        "username": m.username,
                        "raw_username": m.raw_username,
                        "first_name": m.first_name,
                        "last_name": m.last_name,
                        "last_seen_status": m.last_seen_status,
                    }
                    for m in members
                ]
            })

        with open(INITIAL_DATASET_FILE, "w", encoding="utf-8") as f:
            json.dump(seed_data, f, indent=2, ensure_ascii=False)
        print(f"Exported {len(seed_data)} groups with seed members to {INITIAL_DATASET_FILE}")

async def seed_from_file_if_empty():
    """Loads bundled seed data if database has 0 members."""
    if not os.path.exists(INITIAL_DATASET_FILE):
        return

    async with AsyncSessionLocal() as session:
        count = (await session.execute(select(func.count(Member.id)))).scalar_one() or 0
        if count > 0:
            return  # Database already has data

        print(f"Database is empty. Seeding initial data from {INITIAL_DATASET_FILE}...")
        with open(INITIAL_DATASET_FILE, "r", encoding="utf-8") as f:
            seed_data = json.load(f)

        for item in seed_data:
            cat = await get_or_create_category(
                session,
                name=item["category_name"],
                slug=item["category_slug"]
            )
            grp = await upsert_group(
                session=session,
                telegram_id=item["group_telegram_id"],
                title=item["group_title"],
                username=item["group_username"],
                category_id=cat.id,
                member_count=len(item.get("members", [])),
            )
            await session.commit()
            await bulk_save_members(session, grp.id, item.get("members", []))

        print(f"Initial seed data loaded successfully!")

if __name__ == "__main__":
    asyncio.run(export_current_to_seed())
