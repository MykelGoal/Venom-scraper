import datetime
from typing import List, Optional, Tuple
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    UniqueConstraint,
    func,
    select,
    or_,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from config import settings

def get_sanitized_db_url(raw_url: str) -> str:
    """
    Normalizes database URLs for async SQLAlchemy compatibility across Render, Heroku, etc.
    """
    if not raw_url:
        return "sqlite+aiosqlite:///./telegram_directory.db"

    url = raw_url.strip().strip('"').strip("'")

    # Fix typo where 's' was omitted (e.g. 'qlite+aiosqlite' -> 'sqlite+aiosqlite')
    if url.startswith("qlite"):
        url = "s" + url

    # Auto-convert standard SQLite to async SQLite
    if url.startswith("sqlite:///") and not url.startswith("sqlite+aiosqlite:///"):
        url = url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

    # Auto-convert Postgres URLs (Render/Heroku standard) to asyncpg
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    return url

db_url = get_sanitized_db_url(settings.DATABASE_URL)
engine = create_async_engine(db_url, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    groups: Mapped[List["TelegramGroup"]] = relationship("TelegramGroup", back_populates="category")


class TelegramGroup(Base):
    __tablename__ = "telegram_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id"), nullable=False)
    member_count: Mapped[int] = mapped_column(Integer, default=0)
    last_scanned_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    category: Mapped["Category"] = relationship("Category", back_populates="groups")
    memberships: Mapped[List["MemberGroupAssociation"]] = relationship("MemberGroupAssociation", back_populates="group")


class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # stored in lowercase for fast search
    raw_username: Mapped[str] = mapped_column(String(100), nullable=False)          # original case
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_seen_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    groups: Mapped[List["MemberGroupAssociation"]] = relationship("MemberGroupAssociation", back_populates="member")


class MemberGroupAssociation(Base):
    __tablename__ = "member_group_associations"
    __table_args__ = (UniqueConstraint("member_id", "group_id", name="uq_member_group"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(Integer, ForeignKey("members.id", ondelete="CASCADE"), index=True)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("telegram_groups.id", ondelete="CASCADE"), index=True)
    first_seen_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    member: Mapped["Member"] = relationship("Member", back_populates="groups")
    group: Mapped["TelegramGroup"] = relationship("TelegramGroup", back_populates="memberships")


# ---------------- Database Initialization & Seed ----------------

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def seed_default_categories():
    default_categories = [
        ("Crypto & Web3", "crypto", "Blockchain, DeFi, NFTs, and cryptocurrency communities"),
        ("Gaming & Esports", "gaming", "PC/Console gaming, streamers, and competitive esports"),
        ("Betting & Sports", "betting", "Sports betting, prediction markets, and odds discussion"),
        ("Tech & Programming", "tech", "Software development, AI, robotics, and cybersecurity"),
        ("Finance & Trading", "finance", "Stocks, forex, commodities, and investing"),
        ("E-Commerce & Marketing", "marketing", "Dropshipping, digital marketing, and growth hacking"),
    ]
    async with AsyncSessionLocal() as session:
        for name, slug, desc in default_categories:
            stmt = select(Category).where(Category.slug == slug)
            res = await session.execute(stmt)
            if not res.scalar_one_or_none():
                cat = Category(name=name, slug=slug, description=desc)
                session.add(cat)
        await session.commit()


# ---------------- CRUD Operations ----------------

async def get_or_create_category(session: AsyncSession, name: str, slug: str, description: Optional[str] = None) -> Category:
    stmt = select(Category).where(Category.slug == slug)
    res = await session.execute(stmt)
    cat = res.scalar_one_or_none()
    if not cat:
        cat = Category(name=name, slug=slug, description=description)
        session.add(cat)
        await session.flush()
    return cat


async def upsert_group(
    session: AsyncSession,
    telegram_id: int,
    title: str,
    username: Optional[str],
    category_id: int,
    member_count: int = 0,
) -> TelegramGroup:
    stmt = select(TelegramGroup).where(TelegramGroup.telegram_id == telegram_id)
    res = await session.execute(stmt)
    group = res.scalar_one_or_none()
    now = datetime.datetime.now(datetime.timezone.utc)
    if not group:
        group = TelegramGroup(
            telegram_id=telegram_id,
            title=title,
            username=username,
            category_id=category_id,
            member_count=member_count,
            last_scanned_at=now,
        )
        session.add(group)
    else:
        group.title = title
        group.username = username
        group.category_id = category_id
        group.member_count = member_count
        group.last_scanned_at = now
    await session.flush()
    return group


async def bulk_save_members(session: AsyncSession, group_id: int, members_data: List[dict]) -> Tuple[int, int]:
    """
    Saves or updates a batch of members and links them to the specified group.
    Returns (new_members_count, associations_count).
    """
    if not members_data:
        return 0, 0

    new_count = 0
    assoc_count = 0

    # Extract all telegram_ids in this batch
    tg_ids = [m["telegram_id"] for m in members_data]
    
    # Query existing members in database matching these IDs
    stmt = select(Member).where(Member.telegram_id.in_(tg_ids))
    res = await session.execute(stmt)
    existing_members_by_tg_id = {m.telegram_id: m for m in res.scalars().all()}

    # Query existing associations for this group
    existing_member_ids = [m.id for m in existing_members_by_tg_id.values()]
    existing_associations = set()
    if existing_member_ids:
        assoc_stmt = select(MemberGroupAssociation.member_id).where(
            MemberGroupAssociation.group_id == group_id,
            MemberGroupAssociation.member_id.in_(existing_member_ids),
        )
        assoc_res = await session.execute(assoc_stmt)
        existing_associations = set(assoc_res.scalars().all())

    for data in members_data:
        tg_id = data["telegram_id"]
        username = data["username"]
        raw_username = data.get("raw_username", username)
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        last_seen = data.get("last_seen_status")

        member = existing_members_by_tg_id.get(tg_id)
        if not member:
            member = Member(
                telegram_id=tg_id,
                username=username.lower(),
                raw_username=raw_username,
                first_name=first_name,
                last_name=last_name,
                last_seen_status=last_seen,
            )
            session.add(member)
            await session.flush()  # Populates member.id
            existing_members_by_tg_id[tg_id] = member
            new_count += 1
        else:
            # Update info if changed
            member.username = username.lower()
            member.raw_username = raw_username
            member.first_name = first_name
            member.last_name = last_name
            member.last_seen_status = last_seen
            member.updated_at = datetime.datetime.now(datetime.timezone.utc)

        if member.id not in existing_associations:
            assoc = MemberGroupAssociation(member_id=member.id, group_id=group_id)
            session.add(assoc)
            existing_associations.add(member.id)
            assoc_count += 1

    await session.commit()
    return new_count, assoc_count


async def search_directory(
    query: Optional[str] = None,
    category_slug: Optional[str] = None,
    page: int = 1,
    page_size: int = 8,
) -> Tuple[List[dict], int]:
    """
    Searches members by keyword (username, first name, last name) and optional category.
    Returns (list of member dicts, total_count).
    """
    async with AsyncSessionLocal() as session:
        offset = (page - 1) * page_size

        # Base query joining Member, MemberGroupAssociation, TelegramGroup, Category
        stmt = (
            select(
                Member.id,
                Member.raw_username,
                Member.first_name,
                Member.last_name,
                Member.last_seen_status,
                func.group_concat(Category.name, ', ').label("categories"),
                func.group_concat(TelegramGroup.title, ', ').label("groups"),
            )
            .join(MemberGroupAssociation, Member.id == MemberGroupAssociation.member_id)
            .join(TelegramGroup, TelegramGroup.id == MemberGroupAssociation.group_id)
            .join(Category, Category.id == TelegramGroup.category_id)
            .group_by(Member.id, Member.raw_username, Member.first_name, Member.last_name, Member.last_seen_status)
        )

        filters = []
        if query:
            clean_q = query.strip().lower().lstrip("@")
            search_pattern = f"%{clean_q}%"
            filters.append(
                or_(
                    Member.username.like(search_pattern),
                    Member.first_name.ilike(search_pattern),
                    Member.last_name.ilike(search_pattern),
                )
            )

        if category_slug and category_slug != "all":
            filters.append(Category.slug == category_slug)

        if filters:
            stmt = stmt.where(*filters)

        # Count total matching results
        count_subquery = stmt.subquery()
        count_stmt = select(func.count()).select_from(count_subquery)
        total_res = await session.execute(count_stmt)
        total_count = total_res.scalar_one() or 0

        # Fetch paginated items
        paginated_stmt = stmt.order_by(Member.updated_at.desc()).offset(offset).limit(page_size)
        res = await session.execute(paginated_stmt)
        rows = res.all()

        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "username": row[1],
                "first_name": row[2] or "",
                "last_name": row[3] or "",
                "last_seen": row[4] or "unknown",
                "categories": list(set(row[5].split(", "))) if row[5] else [],
                "groups": list(set(row[6].split(", "))) if row[6] else [],
            })

        return results, total_count


async def get_all_categories() -> List[dict]:
    async with AsyncSessionLocal() as session:
        stmt = (
            select(
                Category.id,
                Category.name,
                Category.slug,
                func.count(func.distinct(MemberGroupAssociation.member_id)).label("member_count"),
            )
            .outerjoin(TelegramGroup, TelegramGroup.category_id == Category.id)
            .outerjoin(MemberGroupAssociation, MemberGroupAssociation.group_id == TelegramGroup.id)
            .group_by(Category.id, Category.name, Category.slug)
            .order_by(Category.name)
        )
        res = await session.execute(stmt)
        rows = res.all()
        return [{"id": r[0], "name": r[1], "slug": r[2], "member_count": r[3]} for r in rows]


async def get_directory_stats() -> dict:
    async with AsyncSessionLocal() as session:
        total_members_stmt = select(func.count(Member.id))
        total_groups_stmt = select(func.count(TelegramGroup.id))
        total_categories_stmt = select(func.count(Category.id))

        total_members = (await session.execute(total_members_stmt)).scalar_one() or 0
        total_groups = (await session.execute(total_groups_stmt)).scalar_one() or 0
        total_categories = (await session.execute(total_categories_stmt)).scalar_one() or 0

        return {
            "total_members": total_members,
            "total_groups": total_groups,
            "total_categories": total_categories,
        }
