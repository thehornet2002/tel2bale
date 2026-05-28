from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import PeerIdInvalid, UserNotParticipant
from pyrogram.types import CallbackQuery
from config import ADS_CHANNELS
from utils.keyboards import build_ads_channels
from utils.logger import get_logger

logger = get_logger(__name__)


async def is_member_of_channel(client: Client, message: Message) -> bool:
    """بررسی عضویت کاربر در تمام کانال‌ها — قابل استفاده مستقیم در هندلرها"""
    if not message.from_user:
        return False
    
    # اگر کانال‌های تبلیغی تعریف نشده‌اند، اجازه بدهید
    if not ADS_CHANNELS:
        return True
    
    try:
        for channel in ADS_CHANNELS:
            try:
                member = await client.get_chat_member(
                    chat_id=channel,
                    user_id=message.from_user.id
                )
                if member.status.value not in ("creator", "administrator", "member", 'owner'):
                    await message.reply_text(
                        "لطفا ابتدا در کانال‌های زیر عضو شوید",
                        reply_markup=build_ads_channels(ADS_CHANNELS)
                    )
                    return False
            except (UserNotParticipant, PeerIdInvalid):
                await message.reply_text(
                    "لطفا ابتدا در کانال‌های زیر عضو شوید",
                    reply_markup=build_ads_channels(ADS_CHANNELS)
                )
                return False
        return True
    except Exception as e:
        logger.error(f"خطا در بررسی عضویت کانال: {e}")
        # در صورت خطای نامشخص، رد کنید (محدودیت احتیاطی)
        return False


async def _join_filter_func(_, client: Client, message: Message) -> bool:
    """wrapper با سیگنچر صحیح برای filters.create"""
    return await is_member_of_channel(client, message)


join_filter = filters.create(_join_filter_func)


async def is_member_of_channel_cb(client: Client, callback: CallbackQuery) -> bool:
    """بررسی عضویت کاربر در callback"""
    if not ADS_CHANNELS:
        return True
    
    try:
        for channel in ADS_CHANNELS:
            try:
                member = await client.get_chat_member(
                    chat_id=channel,
                    user_id=callback.from_user.id
                )
                if member.status.value not in ("creator", "administrator", "member", "owner"):
                    await callback.answer("لطفا ابتدا در کانال‌های زیر عضو شوید", show_alert=True)
                    return False
            except (UserNotParticipant, PeerIdInvalid):
                await callback.answer("لطفا ابتدا در کانال‌های زیر عضو شوید", show_alert=True)
                return False
        return True
    except Exception as e:
        logger.error(f"خطا در بررسی عضویت کانال (callback): {e}")
        return False


async def _join_filter_cb_func(_, client: Client, callback: CallbackQuery) -> bool:
    return await is_member_of_channel_cb(client, callback)


join_filter_cb = filters.create(_join_filter_cb_func)
