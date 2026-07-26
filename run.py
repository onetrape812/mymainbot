import asyncio
import os
import sys
import logging
from aiohttp import web

logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

async def handle_health(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_health)
    app.router.add_get("/health", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Web server started on port {port}")

async def run():
    await start_web_server()
    from bot.main import main
    await main()

if __name__ == "__main__":
    try:
        asyncio.run(run())
    except Exception as e:
        logger.error(f"FATAL: {e}", exc_info=True)
        sys.exit(1)
