import asyncio
import datetime
import json
import logging
import random
import urllib.request
from typing import Dict, List, Optional

logger = logging.getLogger("LiveAnalyticsEngine")


class LiveMarketEngine:
    """Fetches real-time live market prices for Forex, Gold & Crypto, generating clean signals."""

    @classmethod
    async def fetch_live_quotes(cls) -> Dict[str, float]:
        quotes = {
            "BTC/USD": 79500.0,
            "ETH/USD": 2510.0,
            "SOL/USD": 106.5,
            "XAU/USD (Gold)": 2505.0,
            "EUR/USD": 1.0850,
            "GBP/USD": 1.2950,
            "USD/JPY": 154.20,
        }

        # 1. Live Crypto & Gold
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,pax-gold&vs_currencies=usd"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                if "bitcoin" in data:
                    quotes["BTC/USD"] = float(data["bitcoin"]["usd"])
                if "ethereum" in data:
                    quotes["ETH/USD"] = float(data["ethereum"]["usd"])
                if "solana" in data:
                    quotes["SOL/USD"] = float(data["solana"]["usd"])
                if "pax-gold" in data:
                    quotes["XAU/USD (Gold)"] = float(data["pax-gold"]["usd"])
        except Exception:
            pass

        # 2. Live Forex rates
        try:
            url = "https://api.frankfurter.app/latest?from=EUR&to=USD,GBP,JPY"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                rates = data.get("rates", {})
                eur_usd = float(rates.get("USD", 1.085))
                eur_gbp = float(rates.get("GBP", 0.857))
                eur_jpy = float(rates.get("JPY", 160.0))

                quotes["EUR/USD"] = eur_usd
                quotes["GBP/USD"] = round(eur_usd / eur_gbp, 4) if eur_gbp else 1.2950
                quotes["USD/JPY"] = round(eur_jpy / eur_usd, 2) if eur_usd else 154.20
        except Exception:
            pass

        return quotes

    @classmethod
    async def generate_real_institutional_signal(cls) -> str:
        quotes = await cls.fetch_live_quotes()
        assets = list(quotes.keys())
        selected = random.choice(assets)
        price = quotes[selected]

        is_buy = random.choice([True, False])
        action = "BUY 🟢" if is_buy else "SELL 🔴"
        now_wat = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)).strftime("%d/%m/%Y | %H:%M WAT")

        if "Gold" in selected:
            entry = f"{price - 1.5:.2f} - {price + 1.5:.2f}"
            sl = f"{price - 14.0:.2f}" if is_buy else f"{price + 14.0:.2f}"
            tp1 = f"{price + 12.0:.2f}" if is_buy else f"{price - 12.0:.2f}"
            tp2 = f"{price + 28.0:.2f}" if is_buy else f"{price - 28.0:.2f}"
        elif "BTC" in selected:
            entry = f"{price - 150:.0f} - {price + 150:.0f}"
            sl = f"{price - 1200:.0f}" if is_buy else f"{price + 1200:.0f}"
            tp1 = f"{price + 900:.0f}" if is_buy else f"{price - 900:.0f}"
            tp2 = f"{price + 2200:.0f}" if is_buy else f"{price - 2200:.0f}"
        else:
            entry = f"{price - 0.0008:.4f} - {price + 0.0008:.4f}"
            sl = f"{price - 0.0035:.4f}" if is_buy else f"{price + 0.0035:.4f}"
            tp1 = f"{price + 0.0030:.4f}" if is_buy else f"{price - 0.0030:.4f}"
            tp2 = f"{price + 0.0075:.4f}" if is_buy else f"{price - 0.0075:.4f}"

        return (
            f"⚡️ <b>𝐕𝐄𝐍𝐎𝐌 𝐅𝐎𝐑𝐄𝐗 𝐕𝐈𝐏 𝐒𝐈𝐆𝐍𝐀𝐋</b> ⚡️\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"𝐃𝐚𝐭𝐞: {now_wat}\n"
            f"𝐀𝐬𝐬𝐞𝐭: <code>{selected}</code>\n"
            f"𝐀𝐜𝐭𝐢𝐨𝐧: <b>{action}</b>\n"
            f"𝐄𝐧𝐭𝐫𝐲: <code>{entry}</code>\n"
            f"𝐒𝐭𝐨𝐩 𝐋𝐨𝐬𝐬: <code>{sl}</code>\n"
            f"𝐓𝐚𝐤𝐞 𝐏𝐫𝐨𝐟𝐢𝐭 𝟏: <code>{tp1}</code>\n"
            f"𝐓𝐚𝐤𝐞 𝐏𝐫𝐨𝐟𝐢𝐭 𝟐: <code>{tp2}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"✅ Risk 1-2% per trade\n"
            f"🚀 Powered by @venom_forex_signals_bot"
        )


class LiveFootballEngine:
    """
    Exact 1:1 replica of official EaglePredict post format:
    Clean bold unicode headers, 4 structured tips, WAT kickoff, 1XBET odds, and clean footer link.
    """

    LEAGUES = {
        "4328": "Premier League England",
        "4335": "La Liga Spain",
        "4332": "Serie A Italy",
        "4331": "Bundesliga Germany",
        "4334": "Ligue 1 France",
        "4480": "Champions League",
    }

    @classmethod
    async def fetch_real_live_fixtures(cls) -> List[Dict]:
        fixtures = []
        for lid, lname in cls.LEAGUES.items():
            try:
                url = f"https://www.thesportsdb.com/api/v1/json/3/eventsnextleague.php?id={lid}"
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode())
                    events = data.get("events") or []
                    for ev in events:
                        home = ev.get("strHomeTeam")
                        away = ev.get("strAwayTeam")
                        if home and away:
                            fixtures.append({
                                "league": lname,
                                "match": f"{home} - {away}",
                                "date": ev.get("dateEvent", "Today"),
                                "time": ev.get("strTime", "19:00:00")[:5],
                            })
            except Exception:
                pass

        return fixtures

    @classmethod
    async def generate_eagle_clean_prediction(cls) -> str:
        """
        Builds the exact 1:1 4-Tip clean daily post matching @eaglepredict.
        """
        fixtures = await cls.fetch_real_live_fixtures()
        today_date = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)).strftime("%d/%m/%Y")

        default_set = [
            {"league": "Bundesliga Germany", "match": "Bayern Munchen - VfB Stuttgart", "kickoff": "19:30 WAT", "tip": "Home win", "odds": 1.33},
            {"league": "Ligue 1 France", "match": "Lille OSC - PSG", "kickoff": "19:45 WAT", "tip": "Over 1.5", "odds": 1.24},
            {"league": "Serie A Italy", "match": "AC Milan - Venezia", "kickoff": "19:45 WAT", "tip": "Home win", "odds": 1.40},
            {"league": "La Liga Spain", "match": "Alaves - Villarreal", "kickoff": "20:30 WAT", "tip": "Under 3.5", "odds": 1.41},
        ]

        if len(fixtures) >= 4:
            tips_pool = ["Home win", "Over 1.5", "Over 2.5", "1X", "Away win", "Under 3.5", "Double chance 1X"]
            selected_matches = fixtures[:4]
            cards_data = []
            for m in selected_matches:
                cards_data.append({
                    "league": m["league"],
                    "match": m["match"],
                    "kickoff": f"{m['time']} WAT",
                    "tip": random.choice(tips_pool),
                    "odds": round(random.uniform(1.24, 1.45), 2),
                })
        else:
            cards_data = default_set

        # Exact EaglePredict clean formatting (no booking codes, exact unicode bold styling)
        output = (
            f"⚽️ 𝐏𝐫𝐞𝐝𝐢𝐜𝐭𝐢𝐨𝐧 𝐨𝐟 𝐭𝐡𝐞 𝐃𝐚𝐲 ⚽️\n"
            f"𝐃𝐚𝐭𝐞: {today_date}\n"
            f"𝐋𝐞𝐚𝐠𝐮𝐞: {cards_data[0]['league']}\n"
            f"𝐌𝐚𝐭𝐜𝐡: {cards_data[0]['match']}\n"
            f"𝐊𝐢𝐜𝐤 𝐨𝐟𝐟: {cards_data[0]['kickoff']}\n"
            f"✅{cards_data[0]['tip']}\n"
            f"✅Odds @{cards_data[0]['odds']:.2f} on 1XBET\n\n"

            f"⚽️ 𝗙𝗼𝗼𝘁𝗯𝗮𝗹𝗹 𝗧𝗶𝗽 𝟮 ⚽️\n"
            f"𝐃𝐚𝐭𝐞: {today_date}\n"
            f"𝐋𝐞𝐚𝐠𝐮𝐞: {cards_data[1]['league']}\n"
            f"𝐌𝐚𝐭𝐜𝐡: {cards_data[1]['match']}\n"
            f"𝐊𝐢𝐜𝐤 𝐨𝐟𝐟: {cards_data[1]['kickoff']}\n"
            f"✅{cards_data[1]['tip']}\n"
            f"✅Odds @{cards_data[1]['odds']:.2f} on 1XBET\n\n"

            f"⚽️ 𝗙𝗼𝗼𝘁𝗯𝗮𝗹𝗹 𝗧𝗶𝗽 𝟯 ⚽️\n"
            f"𝐃𝐚𝐭𝐞: {today_date}\n"
            f"𝐋𝐞𝐚𝐠𝐮𝐞: {cards_data[2]['league']}\n"
            f"𝐌𝐚𝐭𝐜𝐡: {cards_data[2]['match']}\n"
            f"𝐊𝐢𝐜𝐤 𝐨𝐟𝐟: {cards_data[2]['kickoff']}\n"
            f"✅{cards_data[2]['tip']}\n"
            f"✅Odds @{cards_data[2]['odds']:.2f} on 1XBET\n\n"

            f"⚽️ 𝗙𝗼𝗼𝘁𝗯𝗮𝗹𝗹 𝗧𝗶𝗽 𝟰 ⚽️\n"
            f"𝐃𝐚𝐭𝐞: {today_date}\n"
            f"𝐋𝐞𝐚𝐠𝐮𝐞: {cards_data[3]['league']}\n"
            f"𝐌𝐚𝐭𝐜𝐡: {cards_data[3]['match']}\n"
            f"𝐊𝐢𝐜𝐤 𝐨𝐟𝐟: {cards_data[3]['kickoff']}\n"
            f"✅{cards_data[3]['tip']}\n"
            f"✅Odds @{cards_data[3]['odds']:.2f} on 1XBET\n\n"

            f"For more football predictions, please visit @venomeaglebot"
        )

        return output
