import asyncio
import datetime
import os
from typing import List, Optional
from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

DATABASE_URL = os.getenv("PAYWALL_DB_URL", "sqlite+aiosqlite:///./venom_paywall.db")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    price_ngn: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    price_usd: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)  # e.g., 30 for 1 month, 0 for lifetime
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

class Subscriber(Base):
    __tablename__ = "subscribers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), default="Subscriber")
    plan_slug: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    starts_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    payment_reference: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    invite_link: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reference: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    plan_slug: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="NGN")
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, success, failed
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

async def init_paywall_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed standard subscription plans
    async with AsyncSessionLocal() as session:
        plans = [
            ("Monthly VIP Pass", "monthly", 5000.00, 10.00, 30, "🔥 30 Days Full Access to VIP Signals & Community"),
            ("Quarterly VIP Pass", "quarterly", 13500.00, 25.00, 90, "⚡ 90 Days Access (Save 10%)"),
            ("Lifetime VIP Pass", "lifetime", 45000.00, 80.00, 3650, "👑 Permanent Lifetime Access to all VIP channels"),
        ]
        for name, slug, ngn, usd, days, desc in plans:
            res = await session.execute(select(SubscriptionPlan).where(SubscriptionPlan.slug == slug))
            if not res.scalar_one_or_none():
                p = SubscriptionPlan(name=name, slug=slug, price_ngn=ngn, price_usd=usd, duration_days=days, description=desc)
                session.add(p)
        await session.commit()

async def get_plans() -> List[SubscriptionPlan]:
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(SubscriptionPlan))
        return list(res.scalars().all())

async def create_pending_payment(telegram_id: int, plan_slug: str, amount: float, reference: str, currency: str = "NGN") -> PaymentTransaction:
    async with AsyncSessionLocal() as session:
        tx = PaymentTransaction(
            reference=reference,
            telegram_id=telegram_id,
            plan_slug=plan_slug,
            amount=amount,
            currency=currency,
            status="pending",
        )
        session.add(tx)
        await session.commit()
        return tx

async def activate_subscriber(telegram_id: int, username: Optional[str], full_name: str, plan_slug: str, reference: str, invite_link: str, duration_days: int) -> Subscriber:
    async with AsyncSessionLocal() as session:
        # Mark transaction success
        tx_res = await session.execute(select(PaymentTransaction).where(PaymentTransaction.reference == reference))
        tx = tx_res.scalar_one_or_none()
        if tx:
            tx.status = "success"

        now = datetime.datetime.now(datetime.timezone.utc)
        expires = now + datetime.timedelta(days=duration_days) if duration_days > 0 else None

        sub_res = await session.execute(select(Subscriber).where(Subscriber.telegram_id == telegram_id))
        sub = sub_res.scalar_one_or_none()
        if not sub:
            sub = Subscriber(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name,
                plan_slug=plan_slug,
                is_active=True,
                starts_at=now,
                expires_at=expires,
                payment_reference=reference,
                invite_link=invite_link,
            )
            session.add(sub)
        else:
            sub.is_active = True
            sub.plan_slug = plan_slug
            sub.starts_at = now
            sub.expires_at = expires
            sub.payment_reference = reference
            sub.invite_link = invite_link

        await session.commit()
        return sub

async def get_expired_subscribers() -> List[Subscriber]:
    now = datetime.datetime.now(datetime.timezone.utc)
    async with AsyncSessionLocal() as session:
        stmt = select(Subscriber).where(
            Subscriber.is_active == True,
            Subscriber.expires_at != None,
            Subscriber.expires_at <= now,
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())
