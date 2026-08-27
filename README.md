# Telegram Public Community Directory & Search Bot

A high-performance, compliant Telegram member indexer and searchable directory bot. This project crawls public Telegram supergroups, indexes publicly visible usernames of active members, filters out bots and deleted accounts, categorizes users by niche (Crypto, Gaming, Betting, Tech, etc.), and provides a fast interactive Telegram search bot with clickable `t.me` profile links.

---

## 🏛️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Telegram Ecosystem                              │
├──────────────────────────────┬─────────────────────────────────────────┤
│    Public Telegram Groups    │        Telegram Search Users            │
│   (Crypto, Gaming, Tech)     │          (Interactive UI)               │
└──────────────┬───────────────┴────────────────────▲────────────────────┘
               │ (MTProto Userbot API)              │ (Telegram Bot API)
               ▼                                    ▼
┌──────────────────────────────┐        ┌────────────────────────────────┐
│   Telethon Indexer Worker    │        │       Aiogram 3 Search Bot     │
│   - FloodWait Backoff        │        │   - Interactive Category Menu  │
│   - Bot/Deleted Filters      │        │   - Keyword Search (/search)   │
│   - Jittered Sleep Delays    │        │   - Inline Mode Search         │
│   - Session Rotator Pool     │        │   - Clickable t.me Profile URLs│
└──────────────┬───────────────┘        └────────────────▲───────────────┘
               │                                         │
               │ (Async Bulk Upserts)                    │ (Paginated Queries)
               ▼                                         │
┌────────────────────────────────────────────────────────┴───────────────┐
│              SQLAlchemy 2.0 Async Storage Engine                       │
│    SQLite (aiosqlite) for Dev  |  PostgreSQL (asyncpg) for Production  │
│  - Categories  - TelegramGroups  - Members  - MemberGroupAssociations │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Repository Structure

```
├── config.py              # Central configuration via Pydantic & .env
├── database.py            # SQLAlchemy async database models and query layer
├── indexer.py             # Telethon MTProto scraper with jitter & FloodWait safety
├── account_rotator.py     # Multi-account session pool & rotation manager
├── batch_indexer.py       # Batch crawler for bulk group ingestion
├── bot.py                 # Aiogram 3 Telegram Search Bot interface
├── groups.example.json    # Example configuration file for batch scanning
├── test_system.py         # Automated database & search unit tests
├── requirements.txt       # Production dependencies
└── .env.example           # Environment variables template
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites & Installation

Clone the repository and install the dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Credentials (`.env`)

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Fill in your configuration details:

| Variable | Description | Source |
| :--- | :--- | :--- |
| `API_ID` | Telegram API App ID | [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | Telegram API App Hash | [my.telegram.org](https://my.telegram.org) |
| `PHONE_NUMBER` | Phone number for userbot session | Your Telegram number |
| `BOT_TOKEN` | Bot API Token | [@BotFather](https://t.me/BotFather) |
| `DATABASE_URL` | SQLite / PostgreSQL connection URI | `sqlite+aiosqlite:///./telegram_directory.db` |

---

## 🔍 Step-by-Step Usage

### 1. Single Group Crawl via CLI

You can index any public group directly:

```bash
python indexer.py --group eth_developers --category crypto --limit 500
```

- `--group`: Public group handle or link (`eth_developers` or `https://t.me/eth_developers`)
- `--category`: Category slug (`crypto`, `gaming`, `betting`, `tech`, `finance`, `marketing`)
- `--limit`: Maximum member limit to scan in this run (default: 5000)

### 2. Batch Group Crawling

To crawl multiple groups automatically with inter-group rest delays:

1. Copy and modify `groups.example.json` into `groups.json`:
   ```json
   [
     {
       "username": "ethereum",
       "category": "crypto",
       "category_name": "Crypto & Web3",
       "limit": 1000
     },
     {
       "username": "esports_global",
       "category": "gaming",
       "category_name": "Gaming & Esports",
       "limit": 1000
     }
   ]
   ```
2. Execute batch crawler:
   ```bash
   python batch_indexer.py --file groups.json
   ```

### 3. Launching the Search Bot

Start the user-facing Telegram directory bot:

```bash
python bot.py
```

Open your Telegram client and search for your bot:
1. Send `/start` to see the category browser and stats.
2. Send `/search <keyword>` (e.g. `/search alex` or `/search crypto`) to search members.
3. Browse members page by page with direct `t.me/<username>` links.
4. Try inline search: type `@YourBotHandle crypto` in any chat to share profiles directly.

---

## 🛡️ Anti-Flood & Rate Limiting Best Practices

Telegram actively monitors client behavior. The scraper is built with the following safety layers:

1. **Jittered Micro-Delays (`REQUEST_DELAY_MIN` & `REQUEST_DELAY_MAX`)**:
   - Random delays between `3.0s` and `6.0s` after each participant batch to eliminate static bot-like patterns.
2. **Automated `FloodWaitError` Backoff**:
   - Catches MTProto `FloodWaitError` exceptions and pauses execution for the exact penalty seconds specified by Telegram (+ safety margin) before resuming.
3. **Rest Intervals Between Groups (`BATCH_PAUSE_SECONDS`)**:
   - Adds a `30-45s` pause between different group scans so MTProto does not flag aggressive sequential queries.
4. **Member List Permission Handling**:
   - Gracefully handles groups where admins have toggled "Hide Members" or restricted participant visibility (`errors.ChatAdminRequiredError`).
5. **Multi-Session Account Rotator (`account_rotator.py`)**:
   - Distributes requests across a pool of user sessions using round-robin rotation and dynamic cooldown tracking.

---

## 🗄️ Database & Large Dataset Scaling

### Switching from SQLite to PostgreSQL

In `.env`, set:
```ini
DATABASE_URL="postgresql+asyncpg://postgres:yourpassword@localhost:5432/telegram_directory"
```

### Key Schema Optimizations
- **Normalized Many-to-Many Relationships**: A user discovered in multiple groups (e.g. both Crypto and Gaming groups) is stored once in the `members` table and mapped through `member_group_associations`.
- **Indexed Usernames & Lowercase Normalization**: Indexed column queries enable sub-millisecond search across hundreds of thousands of member handles.
- **Batch Upserts**: Members are inserted in chunks of 100 via transactions, reducing database lock overhead.

---

## 🧪 Running Tests

Run the test suite to verify database schemas, queries, and pagination:

```bash
python -m unittest test_system.py
```
