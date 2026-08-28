import datetime
import random
from typing import Dict, List, Optional


class FreeFireAimEngine:
    """
    Venom Free Fire Pro Sensi & Aim-Lock Engine.
    Configured for OB45 / OB46 2026 update with real in-game calibrations,
    One-Tap Headshot Drag techniques, Phone DPI settings, and Weapon Presets.
    """

    # Device Calibrations (0-100 & 0-200 slider compatibility)
    PHONE_CALIBRATIONS = {
        "iphone": {
            "device": "iPhone (11 / 12 / 13 / 14 / 15 / 16 Series)",
            "general": 98,
            "red_dot": 96,
            "scope_2x": 92,
            "scope_4x": 88,
            "sniper": 60,
            "free_look": 72,
            "dpi": "Default (Touch Sensitivity: MAX)",
            "fire_btn_size": "43%",
            "fire_btn_pos": "Lower Right (Height: 18%)",
            "pointer_speed": "Maximum (Tracking speed on iOS)",
            "drag_type": "Fast J-Drag / Quick Flick",
            "best_graphic": "Ultra + High FPS (120Hz ProMotion)"
        },
        "samsung": {
            "device": "Samsung Galaxy (A14-A55, S21-S24, Ultra)",
            "general": 100,
            "red_dot": 98,
            "scope_2x": 94,
            "scope_4x": 90,
            "sniper": 64,
            "free_look": 80,
            "dpi": "480 - 560 DPI (Developer Options)",
            "fire_btn_size": "48%",
            "fire_btn_pos": "Bottom Right (Height: 20%)",
            "pointer_speed": "Max + Primary mouse button set to Left",
            "drag_type": "Straight Up Drag (Smooth thumb release)",
            "best_graphic": "Smooth + High FPS (60/90Hz)"
        },
        "redmi_xiaomi": {
            "device": "Redmi / Xiaomi / POCO (Note 10-13, X3-X6 Pro)",
            "general": 99,
            "red_dot": 97,
            "scope_2x": 93,
            "scope_4x": 89,
            "sniper": 62,
            "free_look": 78,
            "dpi": "450 - 520 DPI (Smallest Width)",
            "fire_btn_size": "46%",
            "fire_btn_pos": "Mid-Bottom Right (Height: 22%)",
            "pointer_speed": "Max + Touch Sampling on 480Hz in Game Turbo",
            "drag_type": "Hook Drag / C-Drag for SMGs",
            "best_graphic": "Smooth + High FPS (Game Turbo Extreme)"
        },
        "infinix_tecno": {
            "device": "Infinix / TECNO / Itel (Hot, Note, Spark, Camon)",
            "general": 100,
            "red_dot": 100,
            "scope_2x": 95,
            "scope_4x": 92,
            "sniper": 66,
            "free_look": 82,
            "dpi": "480 - 580 DPI",
            "fire_btn_size": "50%",
            "fire_btn_pos": "Bottom Right (Height: 20%)",
            "pointer_speed": "Maximum",
            "drag_type": "U-Drag curve swipe",
            "best_graphic": "Smooth + Ultra FPS (Enable High Touch Rate)"
        },
        "pc_emulator": {
            "device": "PC BlueStacks 5 / MSI App Player / LDPlayer",
            "general": 82,
            "red_dot": 78,
            "scope_2x": 72,
            "scope_4x": 68,
            "sniper": 48,
            "free_look": 65,
            "dpi": "Mouse DPI: 1000 | In-Game X: 1.45, Y: 0.85 (Tweaks: 16450)",
            "fire_btn_size": "15%",
            "fire_btn_pos": "Default Keymap Position",
            "pointer_speed": "6/11 Windows pointer speed (Enhanced precision OFF)",
            "drag_type": "Micro-flick with wrist rotation",
            "best_graphic": "Ultra + High FPS (90/120/240 FPS Unlock)"
        }
    }

    # Weapon One-Tap Rules
    WEAPON_TACTICS = {
        "m1887": {
            "name": "M1887 Shotgun (Double Barrel)",
            "technique": "V-Drag & Quick Switch",
            "aim_placement": "White Crosshair placed near enemy feet, then flick V-shape upward.",
            "fire_btn_size": "42% - 46%",
            "skill_combo": "Tatsuya + Hayato + Kelly + Caroline (High Agility & Armor Penetration)"
        },
        "deagle": {
            "name": "Desert Eagle (One-Tap God Gun)",
            "technique": "Straight Vertical J-Drag",
            "aim_placement": "Keep red crosshair beside chest, do sudden sharp upward flick with thumb release.",
            "fire_btn_size": "44% - 48%",
            "skill_combo": "Alok / Tatsuya + Moco + Hayato + Kelly"
        },
        "woodpecker": {
            "name": "Woodpecker / AC80 / SVD (DMR One-Tap)",
            "technique": "Micro-Flick Drag",
            "aim_placement": "Aim slightly above shoulder level, single tap drag.",
            "fire_btn_size": "45%",
            "skill_combo": "Rafael (Silent DMR bleed) + Laura + Kelly + Moco"
        },
        "mp40_ump": {
            "name": "MP40 & UMP (SMG Pure Red Spray)",
            "technique": "Rotation / Hook Drag",
            "aim_placement": "Chest level drag following enemy movement vector.",
            "fire_btn_size": "46% - 50%",
            "skill_combo": "Tatsuya + D-Bee + Hayato + Luna (Extreme Fire Rate)"
        }
    }

    @classmethod
    def get_device_config(cls, query: str = "iphone") -> str:
        q = query.lower()
        key = "samsung"
        for k in cls.PHONE_CALIBRATIONS:
            if k in q or (k == "redmi_xiaomi" and ("redmi" in q or "xiaomi" in q or "poco" in q)) or (k == "infinix_tecno" and ("infinix" in q or "tecno" in q or "itel" in q)):
                key = k
                break
            elif "iphone" in q or "ios" in q or "apple" in q:
                key = "iphone"
                break
            elif "pc" in q or "emulator" in q or "bluestacks" in q:
                key = "pc_emulator"
                break

        cfg = cls.PHONE_CALIBRATIONS[key]
        return (
            f"🎯 <b>FREE FIRE PRO AIMBOT / 100% HEADSHOT SENSI</b> 🎯\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📱 <b>Device:</b> <code>{cfg['device']}</code>\n"
            f"⚡ <b>Update:</b> OB45 / 2026 Calibrated (Pure Red Numbers)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎛️ <b>IN-GAME SENSITIVITY SLIDERS:</b>\n"
            f"• <b>General:</b> <code>{cfg['general']}</code>\n"
            f"• <b>Red Dot:</b> <code>{cfg['red_dot']}</code>\n"
            f"• <b>2X Scope:</b> <code>{cfg['scope_2x']}</code>\n"
            f"• <b>4X Scope:</b> <code>{cfg['scope_4x']}</code>\n"
            f"• <b>Sniper Scope:</b> <code>{cfg['sniper']}</code>\n"
            f"• <b>Free Look:</b> <code>{cfg['free_look']}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚙️ <b>PRO HARDWARE & HUD CALIBRATION:</b>\n"
            f"• <b>DPI Setting:</b> <code>{cfg['dpi']}</code>\n"
            f"• <b>Fire Button Size:</b> <code>{cfg['fire_btn_size']}</code>\n"
            f"• <b>Fire Button Pos:</b> {cfg['fire_btn_pos']}\n"
            f"• <b>Pointer Speed:</b> {cfg['pointer_speed']}\n"
            f"• <b>Graphics:</b> {cfg['best_graphic']}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔥 <b>SECRET AIM-LOCK TECHNIQUE:</b>\n"
            f"👉 <b>{cfg['drag_type']}</b>\n"
            f"📌 Keep white crosshair near the ground/feet before dragging up to lock directly on the head without shaking!\n\n"
            f"👑 Powered by Venom Gaming AI Matrix"
        )

    @classmethod
    def get_weapon_guide(cls, weapon_key: str = "m1887") -> str:
        w_key = "m1887"
        q = weapon_key.lower()
        if "deagle" in q or "desert" in q:
            w_key = "deagle"
        elif "wood" in q or "ac80" in q or "svd" in q:
            w_key = "woodpecker"
        elif "mp40" in q or "ump" in q or "smg" in q:
            w_key = "mp40_ump"

        w = cls.WEAPON_TACTICS[w_key]
        return (
            f"💥 <b>ONE-TAP HEADSHOT GUIDE: {w['name']}</b> 💥\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 <b>Drag Technique:</b> {w['technique']}\n"
            f"🔘 <b>Fire Button Size:</b> <code>{w['fire_btn_size']}</code>\n"
            f"🎯 <b>Crosshair Placement:</b>\n"
            f"• {w['aim_placement']}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👑 <b>BEST CHARACTER SKILL COMBO:</b>\n"
            f"• {w['skill_combo']}\n\n"
            f"🚀 100% Red Numbers Only • Anti-Recoil Verified"
        )
