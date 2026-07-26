import asyncio
import os
from aiohttp import web
from bot.main import main

async def handle_health(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_health)
    app.router.add_get("/health", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8080)))
    await site.start()

async def run():
    await start_web_server()
    await main()

if __name__ == "__main__":
    asyncio.run(run())
