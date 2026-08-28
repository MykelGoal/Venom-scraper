import random
import datetime

class SignalGenerator:
    """Generates professionally formatted Forex trading signals and Football predictions."""

    # ---------------- 1. FOREX SIGNALS ----------------
    FOREX_PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "XAU/USD (Gold)", "BTC/USD", "GBP/JPY", "AUD/USD", "US30 (Dow Jones)"]
    ACTIONS = ["BUY 🟢", "SELL 🔴", "BUY LIMIT 🟢", "SELL LIMIT 🔴"]

    @classmethod
    def generate_forex_signal(cls) -> str:
        pair = random.choice(cls.FOREX_PAIRS)
        action = random.choice(cls.ACTIONS)
        is_gold = "Gold" in pair
        is_crypto = "BTC" in pair
        is_us30 = "US30" in pair

        if is_gold:
            entry = round(random.uniform(2450.0, 2520.0), 2)
            sl = round(entry - 15.0 if "BUY" in action else entry + 15.0, 2)
            tp1 = round(entry + 10.0 if "BUY" in action else entry - 10.0, 2)
            tp2 = round(entry + 25.0 if "BUY" in action else entry - 25.0, 2)
            tp3 = round(entry + 45.0 if "BUY" in action else entry - 45.0, 2)
        elif is_crypto:
            entry = round(random.uniform(62000.0, 68000.0), 1)
            sl = round(entry - 1200.0 if "BUY" in action else entry + 1200.0, 1)
            tp1 = round(entry + 800.0 if "BUY" in action else entry - 800.0, 1)
            tp2 = round(entry + 2000.0 if "BUY" in action else entry - 2000.0, 1)
            tp3 = round(entry + 3500.0 if "BUY" in action else entry - 3500.0, 1)
        elif is_us30:
            entry = round(random.uniform(40000.0, 41500.0), 0)
            sl = round(entry - 200.0 if "BUY" in action else entry + 200.0, 0)
            tp1 = round(entry + 150.0 if "BUY" in action else entry - 150.0, 0)
            tp2 = round(entry + 350.0 if "BUY" in action else entry - 350.0, 0)
            tp3 = round(entry + 600.0 if "BUY" in action else entry - 600.0, 0)
        else:
            entry = round(random.uniform(1.0500, 1.3200), 4)
            sl = round(entry - 0.0040 if "BUY" in action else entry + 0.0040, 4)
            tp1 = round(entry + 0.0030 if "BUY" in action else entry - 0.0030, 4)
            tp2 = round(entry + 0.0075 if "BUY" in action else entry - 0.0075, 4)
            tp3 = round(entry + 0.0150 if "BUY" in action else entry - 0.0150, 4)

        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M UTC")

        signal_text = (
            f"⚡ <b>VENOM FOREX VIP SIGNAL</b> ⚡\n\n"
            f"📊 <b>Asset:</b> <code>{pair}</code>\n"
            f"🎯 <b>Action:</b> <b>{action}</b>\n\n"
            f"📍 <b>Entry Price:</b> <code>{entry}</code>\n"
            f"🛑 <b>Stop Loss (SL):</b> <code>{sl}</code>\n\n"
            f"🎯 <b>Take Profit 1:</b> <code>{tp1}</code> (Scalp)\n"
            f"🎯 <b>Take Profit 2:</b> <code>{tp2}</code> (Day Trade)\n"
            f"🎯 <b>Take Profit 3:</b> <code>{tp3}</code> (Runner)\n\n"
            f"⚖️ <b>Risk Management:</b> Use 1-2% max risk\n"
            f"🕒 <b>Time:</b> <i>{now_str}</i>\n\n"
            f"🚀 <i>Powered by Venom Tech Signals</i>"
        )
        return signal_text

    # ---------------- 2. FOOTBALL PREDICTIONS ----------------
    MATCHES = [
        ("Arsenal vs Chelsea", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League", "Home Win (Arsenal) & Over 1.5", 1.85),
        ("Real Madrid vs Barcelona", "🇪🇸 La Liga", "Both Teams to Score (BTTS) & Over 2.5", 1.95),
        ("Bayern Munich vs Dortmund", "🇩🇪 Bundesliga", "Over 3.5 Goals", 2.10),
        ("Man City vs Liverpool", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League", "Over 2.5 Goals", 1.65),
        ("PSG vs Marseille", "🇫🇷 Ligue 1", "Home Win (PSG) & Over 2.5", 1.80),
        ("Inter Milan vs Juventus", "🇮🇹 Serie A", "Under 2.5 Goals", 1.75),
    ]

    @classmethod
    def generate_football_prediction(cls) -> str:
        match, league, tip, odds = random.choice(cls.MATCHES)
        confidence = random.choice(["⭐⭐⭐⭐⭐ (95% High Confidence)", "⭐⭐⭐⭐ (85% Solid Pick)"])

        # Generate realistic mock booking codes
        sporty_code = f"BC{random.randint(10000, 99999)}"
        bet9ja_code = f"{random.randint(10, 99)}X{random.choice('ABCDEF')}{random.randint(100, 999)}"
        onexbet_code = f"{random.choice('XYZ')}{random.randint(1000, 9999)}"

        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        prediction_text = (
            f"⚽ <b>VENOM DAILY FOOTBALL BANKER</b> ⚽\n\n"
            f"🏆 <b>League:</b> {league}\n"
            f"⚔️ <b>Match:</b> <b>{match}</b>\n\n"
            f"🎯 <b>Prediction:</b> <code>{tip}</code>\n"
            f"📈 <b>Odds:</b> <b>{odds:.2f}</b>\n"
            f"🔥 <b>Confidence:</b> {confidence}\n\n"
            f"🎟️ <b>BOOKING CODES:</b>\n"
            f"• <b>SportyBet:</b> <code>{sporty_code}</code>\n"
            f"• <b>Bet9ja:</b> <code>{bet9ja_code}</code>\n"
            f"• <b>1xBet:</b> <code>{onexbet_code}</code>\n\n"
            f"🕒 <i>{now_str}</i>\n"
            f"💎 <i>Join VIP for 10+ Daily Banker Odds! Powered by Venom Tech</i>"
        )
        return prediction_text
