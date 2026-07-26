import os
from pathlib import Path

if os.getenv("RENDER"):
    pass
else:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
BOT_USERNAME = os.getenv("BOT_USERNAME", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "")

if os.getenv("RENDER"):
    DATABASE_URL = "sqlite+aiosqlite:////tmp/bot.db"
else:
    DATABASE_URL = f"sqlite+aiosqlite:///{Path(__file__).resolve().parent.parent / 'data' / 'bot.db'}"

PAGE_SIZE = 5
MAX_REVIEW_LENGTH = 1000
REVIEWS_PER_PAGE = 5
