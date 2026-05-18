from pyrogram import Client
from config import TEL_API_ID, TEL_API_HASH, TEL_BOT_TOKEN, ADMIN_IDS
from db.model_sync import create_tables as create_tables_sync
from db.model_sync import add_user as add_user_sync
plugins = dict(root="handlers")



telapp = Client(
    "bot",
    api_id=TEL_API_ID,
    api_hash=TEL_API_HASH,
    bot_token=TEL_BOT_TOKEN,
    plugins=plugins,
    proxy=dict(scheme="socks5", hostname="127.0.0.1", port=10998),
)

if __name__ == "__main__":
    create_tables_sync()
    for admin_id in ADMIN_IDS:
        add_user_sync(admin_id,True)
    telapp.run()
