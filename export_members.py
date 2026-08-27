import asyncio
import csv
import json
import os
import sys
from sqlalchemy import select
from database import AsyncSessionLocal, Member, MemberGroupAssociation, TelegramGroup, Category

async def export_members(output_format: str = "csv", category_slug: str = None, filename: str = None):
    async with AsyncSessionLocal() as session:
        stmt = (
            select(
                Member.telegram_id,
                Member.raw_username,
                Member.first_name,
                Member.last_name,
                Member.last_seen_status,
                TelegramGroup.title.label("group_title"),
                Category.name.label("category_name"),
            )
            .join(MemberGroupAssociation, Member.id == MemberGroupAssociation.member_id)
            .join(TelegramGroup, TelegramGroup.id == MemberGroupAssociation.group_id)
            .join(Category, Category.id == TelegramGroup.category_id)
        )

        if category_slug and category_slug != "all":
            stmt = stmt.where(Category.slug == category_slug)

        res = await session.execute(stmt)
        rows = res.all()

        if not rows:
            print(f"No members found to export (filter: category={category_slug}).")
            return None

        if not filename:
            cat_tag = category_slug if category_slug else "all"
            filename = f"exported_members_{cat_tag}.{output_format}"

        if output_format == "csv":
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Telegram_ID", "Username", "Profile_Link", "First_Name", "Last_Name", "Last_Seen", "Group", "Category"])
                for r in rows:
                    writer.writerow([
                        r.telegram_id,
                        f"@{r.raw_username}",
                        f"https://t.me/{r.raw_username}",
                        r.first_name or "",
                        r.last_name or "",
                        r.last_seen_status or "unknown",
                        r.group_title,
                        r.category_name,
                    ])
        elif output_format == "txt":
            with open(filename, "w", encoding="utf-8") as f:
                for r in rows:
                    f.write(f"@{r.raw_username} | https://t.me/{r.raw_username} | {r.first_name} {r.last_name} | [{r.category_name}]\n")
        elif output_format == "json":
            data = [
                {
                    "telegram_id": r.telegram_id,
                    "username": f"@{r.raw_username}",
                    "profile_url": f"https://t.me/{r.raw_username}",
                    "first_name": r.first_name,
                    "last_name": r.last_name,
                    "last_seen": r.last_seen_status,
                    "group": r.group_title,
                    "category": r.category_name,
                }
                for r in rows
            ]
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Successfully exported {len(rows)} members to '{filename}'!")
        return filename

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Export indexed members to file")
    parser.add_argument("--format", choices=["csv", "txt", "json"], default="csv", help="Output format")
    parser.add_argument("--category", type=str, default=None, help="Filter by category slug (e.g. betting, crypto, tech)")
    parser.add_argument("--out", type=str, default=None, help="Output file name")
    args = parser.parse_args()

    asyncio.run(export_members(output_format=args.format, category_slug=args.category, filename=args.out))
