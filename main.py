import asyncio

from pyrogram import Client, idle
from pyrogram.types import BotCommand

from config import TEL_API_ID, TEL_API_HASH, TEL_BOT_TOKEN, ADMIN_IDS, TELPROXY
from db.model_sync import create_tables as create_tables_sync
from db.model_sync import add_user as add_user_sync
from utils.logger import setup_logger

plugins = dict(root="handlers")


telapp = Client(
    "bot",
    api_id=TEL_API_ID,
    api_hash=TEL_API_HASH,
    bot_token=TEL_BOT_TOKEN,
    plugins=plugins,
    proxy=TELPROXY,
)


async def setup_bot_commands():
    await telapp.set_bot_commands([
        BotCommand("start", "شروع ربات"),
        BotCommand("help", "راهنمای استفاده از ربات"),
    ])


async def main():
    setup_logger()
    create_tables_sync()
    for admin_id in ADMIN_IDS:
        add_user_sync(admin_id, True)
    await telapp.start()
    await setup_bot_commands()
    await idle()
    await telapp.stop()

if __name__ == "__main__":
    asyncio.run(main())