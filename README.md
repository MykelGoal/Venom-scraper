# 🕷️ VENOM TECH — MULTI-BOT ECOSYSTEM

[![Render Status](https://img.shields.io/badge/Render-Deploy%20Ready-46E3B7?logo=render&logoColor=white)](https://render.com)
[![Telegram Bots](https://img.shields.io/badge/Telegram-3%20Live%20Bots-2CA5E0?logo=telegram&logoColor=white)](https://t.me/venomscraperbot)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An institutional-grade, multi-bot Telegram ecosystem powered by live market feeds, real-time football intelligence, and high-performance MTProto group indexing.

---

## 🤖 The Active Bot Fleet

| Bot | Handle | Core Function |
| :--- | :--- | :--- |
| **🔍 Directory Scraper** | [@venomscraperbot](https://t.me/venomscraperbot) | Public group directory, user discovery & niche search |
| **⚡ Forex VIP Signals** | [@venom_forex_signals_bot](https://t.me/venom_forex_signals_bot) | Live Gold & Forex SMC signals + Auto-channel posting |
| **🦅 Eagle Predictions** | [@venomeaglebot](https://t.me/venomeaglebot) | 1:1 EaglePredict daily bankers + Auto-channel posting |

---

## ⚡ 1-Click Deploy to Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### Required Environment Variables

Add these in **Render Dashboard ➡️ Environment**:

```ini
# Core Telegram API (from https://my.telegram.org)
API_ID=39706152
API_HASH=749a3068f8318dcd70efb7a88d796c11
TELEGRAM_STRING_SESSION=1BJWap1wBu4-6xtT7BJTQPe0KzeHV8QE0Ylw_vSiSNGe2Leo5Wpbj5UQlyN8ef9IEeHQxS0yotsbqpU8_wC-yjcAOMevK16OEpYnYJGLhb8FXd4P46mvnshal4H-4kgG7--apCEl1XjRMeuOS5C7PPs5YtviK7fyglB1SOQ-ADPD4omY6I3XiD12GDyFkQ9RvfMBQPIJqvjahMyE93Pt1ij41rCOmxJJgN5bhy7bKXIYX5Wxu3vde1IlVVKEsDHtUN9jNqsjACqbd-w24WNfhAN54AXnKwWHFqEYlr6fyb_JScqTNdnUDpp5Snd5BkKfgPYOFGfjctOoSFWyvmB126PvnGr8d_dc=

# Bot API Tokens (from @BotFather)
BOT_TOKEN=8872020288:AAHbHL2pcTjcNV6jlO7N-HdG8BbV0NfeEjk
FOREX_BOT_TOKEN=8967863227:AAFVno4s0e3WkD5XGGNBJakGNU3O4kLOBEI
PREDICTION_BOT_TOKEN=8712477067:AAEKbiPxgzYwsOVUx5wM6F5gboB9s32e5l8

# Database (PostgreSQL or SQLite)
DATABASE_URL=sqlite+aiosqlite:///./telegram_directory.db
```

---

## 💻 Local Quickstart (Run All Bots in 3 Steps)

```bash
# 1. Clone & install dependencies
git clone https://github.com/MykelGoal/Venom-scraper.git
cd Venom-scraper && pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env

# 3. Launch the entire multi-bot network concurrently
python3 run_bot_network.py
```

---

## 📢 Hands-Free Auto-Posting to Channels

Both **Venom Forex** and **Venom Eagle Predictions** support automatic broadcasting:

1. Add **[@venomeaglebot](https://t.me/venomeaglebot)** or **[@venom_forex_signals_bot](https://t.me/venom_forex_signals_bot)** as an **Administrator** to your Telegram Channel.
2. Grant **"Post Messages"** permission.
3. The bot **instantly links** and automatically posts clean daily slips or market signals on schedule!

---

## 🛡️ Key Features

- **Institutional Analytics:** Live CoinGecko, ECB & TheSportsDB feeds (zero fake static data).
- **Exact EaglePredict Layout:** Clean unicode typography, WAT kickoff, and 1XBET odds.
- **SMC Forex Setups:** Entry zones, SL, TP1–TP3 with precise pip calculations and order block rationale.
- **24/7 Persistent Storage:** Zero data loss across restarts via unified `DATABASE_URL` (Postgres / SQLite).

---

<p align="center">
  <b>Built with ❤️ by Venom Tech</b> • <i>Clean, Modular & High-Converting</i>
</p>
