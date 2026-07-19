"""
هندلرهای مربوط به کانال‌های جوین اجباری (ads channel): افزودن، حذف و اعتبارسنجی.
"""
import re
from urllib.parse import urlparse
from pyrogram.types import Message
from pyrogram.errors import ChannelInvalid, ChannelPrivate, PeerIdInvalid, UsernameInvalid, UsernameNotOccupied
from db import model_async
from config import add_ads_channel, remove_ads_channel
from utils.keyboards import build_back_management_keyboard
from handlers.handler_helpers.message_helpers.common import admin_only


def normalize_telegram_channel_input(raw_value: str) -> str | int | None:
    value = (raw_value or "").strip()

    if not value:
        return None

    value = value.split()[0]

    if value.startswith("http://") or value.startswith("https://"):
        parsed = urlparse(value)
        host = parsed.netloc.lower()
        path = parsed.path.strip("/")

        if host not in ("t.me", "telegram.me", "www.t.me", "www.telegram.me"):
            return None

        if not path:
            return None

        if path.startswith("+") or path.startswith("joinchat/"):
            return None

        value = path.split("/")[0]

    elif value.startswith("t.me/") or value.startswith("telegram.me/"):
        value = value.split("/", 1)[1].strip("/").split("/")[0]

    value = value.strip()

    if value.startswith("@"):
        value = value[1:]

    if re.fullmatch(r"-?\d+", value):
        return int(value)

    if not re.fullmatch(r"[A-Za-z0-9_]{5,32}", value):
        return None

    return f"@{value}"


def ads_channel_aliases(raw_value: str, normalized_value: str | int | None = None) -> set[str]:
    aliases: set[str] = set()

    if raw_value:
        raw = raw_value.strip()
        aliases.add(raw)
        aliases.add(raw.lstrip("@"))

    if normalized_value is not None:
        aliases.add(str(normalized_value))
        if isinstance(normalized_value, str):
            aliases.add(normalized_value.lstrip("@"))

    return {item for item in aliases if item}


async def resolve_and_validate_ads_channel(message: Message, raw_value: str) -> tuple[str | None, str | None]:
    normalized = normalize_telegram_channel_input(raw_value)

    if normalized is None:
        return None, (
            "فرمت کانال معتبر نیست.\n\n"
            "فرمت‌های قابل قبول:\n"
            "@channel\n"
            "channel\n"
            "https://t.me/channel\n"
            "-1001234567890"
        )

    try:
        chat = await message._client.get_chat(normalized)
    except (UsernameInvalid, UsernameNotOccupied, PeerIdInvalid, ChannelInvalid):
        return None, "کانالی با این مشخصات پیدا نشد."
    except ChannelPrivate:
        return None, (
            "کانال خصوصی است یا ربات به آن دسترسی ندارد.\n"
            "ابتدا ربات را عضو کانال کنید، سپس دوباره تلاش کنید."
        )
    except Exception as e:
        return None, f"خطا در بررسی کانال:\n{e}"

    chat_id = chat.id

    try:
        member = await message._client.get_chat_member(chat_id, "me")
    except Exception:
        return None, (
            "ربات در این کانال عضو نیست یا دسترسی بررسی عضویت ندارد.\n"
            "ابتدا ربات را به کانال اضافه کنید."
        )

    status_value = getattr(member.status, "value", str(member.status))

    if status_value not in ("creator", "administrator", "member", "owner"):
        return None, "ربات در این کانال عضو نیست."

    if getattr(chat, "username", None):
        return f"@{chat.username}", None

    return str(chat_id), None


@admin_only
async def enter_join_ads_channel(message: Message, user_id: int):
    channel_value, error = await resolve_and_validate_ads_channel(message, message.text or "")
    if error:
        await message.reply_text(error, reply_markup=build_back_management_keyboard())
        return

    if not await add_ads_channel(channel_value):
        await message.reply_text('این کانال قبلاً در لیست Join اجباری ثبت شده است.', reply_markup=build_back_management_keyboard())
        return

    await model_async.set_state(user_id, 'management')
    await message.reply_text(
        f'کانال با موفقیت اضافه شد.\nشناسه ذخیره‌شده: {channel_value}',
        reply_markup=build_back_management_keyboard()
    )


@admin_only
async def enter_delete_join_ads(message: Message, user_id: int):
    channel_value, _ = await resolve_and_validate_ads_channel(message, message.text or "")

    removed = False
    for alias in ads_channel_aliases(message.text or "", channel_value):
        if await remove_ads_channel(alias):
            removed = True
            break

    if not removed:
        await message.reply_text('این کانال در لیست Join اجباری پیدا نشد.', reply_markup=build_back_management_keyboard())
        return

    await model_async.set_state(user_id, 'management')
    await message.reply_text('کانال با موفقیت حذف شد.', reply_markup=build_back_management_keyboard())