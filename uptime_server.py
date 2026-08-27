import asyncio
import logging
import aiohttp
from aiohttp import web
from config import settings
from database import get_directory_stats

logger = logging.getLogger("UptimeServer")

async def health_check_handler(request):
    try:
        stats = await get_directory_stats()
        return web.json_response({
            "status": "online",
            "bot": "VENOM SCRAPER",
            "service": "active",
            "stats": stats,
        })
    except Exception as e:
        return web.json_response({
            "status": "degraded",
            "error": str(e)
        }, status=500)

async def self_ping_worker(url: str, interval_seconds: int = 600):
    """
    Pings the Render/Koyeb external URL every 10 minutes to prevent the free instance from sleeping.
    """
    logger.info(f"Self-ping worker started for: {url} (every {interval_seconds}s)")
    # Wait initial 30s before first ping
    await asyncio.sleep(30)

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(url, timeout=15) as resp:
                    logger.info(f"Self-ping to {url} returned HTTP {resp.status}")
            except Exception as e:
                logger.warning(f"Self-ping failed: {e}")
            await asyncio.sleep(interval_seconds)

async def start_uptime_web_server(port: int = 8080):
    app = web.Application()
    app.router.add_get("/", health_check_handler)
    app.router.add_get("/health", health_check_handler)
    app.router.add_get("/ping", health_check_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Uptime Health HTTP server running on 0.0.0.0:{port}")

    if settings.PING_URL:
        asyncio.create_task(self_ping_worker(settings.PING_URL, interval_seconds=600))
    else:
        logger.info("No PING_URL or RENDER_EXTERNAL_URL set. Set PING_URL to enable automatic self-pinging.")
