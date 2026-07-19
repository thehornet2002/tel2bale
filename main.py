import asyncio

from pyrogram import Client, idle
from pyrogram.types import BotCommand

from config import (
    TEL_API_ID,
    TEL_API_HASH,
    TEL_BOT_TOKEN,
    ADMIN_IDS,
    TELPROXY,
    SUPPORT_GROUP,
    set_support_message_enabled,
)
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


#This section only registers commands for user use (the handlers don’t run here).
async def setup_bot_commands():
    await telapp.set_bot_commands([
        BotCommand("start", "شروع ربات"),
        BotCommand("help", "راهنمای استفاده از ربات"),
    ])

async def check_support_group_membership():
    """
    بررسی می‌کند آیا ربات عضو گروه پشتیبانی (SUPPORT_GROUP) هست یا نه.
    نتیجه در SUPPORT_MESSAGE ذخیره می‌شود و گزینه «پیام به پشتیبانی»
    فقط در صورت عضویت واقعی ربات در گروه، در منو نمایش داده می‌شود.
    """
    if not SUPPORT_GROUP:
        await set_support_message_enabled(False)
        return

    try:
        me = await telapp.get_me()
        member = await telapp.get_chat_member(int(SUPPORT_GROUP), me.id)
        enabled = member.status.value in ("member", "administrator", "creator", "owner")
    except Exception:
        enabled = False

    await set_support_message_enabled(enabled)


#Program entry point
async def main():
    setup_logger()
    create_tables_sync()
    for admin_id in ADMIN_IDS:
        add_user_sync(admin_id, True)
    await telapp.start()
    await check_support_group_membership()
    await setup_bot_commands()
    await idle()
    await telapp.stop()

if __name__ == "__main__":
    asyncio.run(main())