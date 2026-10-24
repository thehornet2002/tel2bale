"""
Handlers for user S3 storage credential configuration.
"""
import re
from pyrogram.types import Message
from db import model_async
from services import s3_service
from utils.keyboards import build_back_keyboard
from utils.parser import validate_link
from handlers.handler_helpers.message_helpers.common import _PENDING_S3, _PENDING_CONFIG


async def set_s3_access_key(message: Message, user_id: int):
    text = (message.text or "").strip()
    if not text or len(text) > 128 or not re.match(r"^[A-Za-z0-9_\-\.+=/]+$", text):
        await message.reply_text('فرمت Access Key نامعتبر است. لطفاً مقدار صحیح را وارد کنید.', reply_markup=build_back_keyboard())
        return

    _PENDING_S3[user_id] = {"access_key": text}
    await model_async.set_state(user_id, 'set_s3_secret_key')
    await message.reply_text('لطفا Secret Key را وارد نمایید.', reply_markup=build_back_keyboard())


async def set_s3_secret_key(message: Message, user_id: int):
    text = (message.text or "").strip()
    if not text or len(text) > 256 or any(c.isspace() for c in text):
        await message.reply_text('فرمت Secret Key نامعتبر است. لطفاً مقدار صحیح را وارد کنید.', reply_markup=build_back_keyboard())
        return

    if user_id not in _PENDING_S3:
        _PENDING_S3[user_id] = {}
    _PENDING_S3[user_id]["secret_key"] = text

    await model_async.set_state(user_id, 'set_s3_endpoint')
    await message.reply_text(
        'لطفا S3 EndPoint را به صورت لینک وارد کنید.',
        reply_markup=build_back_keyboard()
    )


async def set_s3_endpoint(message: Message, user_id: int):
    endpoint_url = await validate_link(message.text)
    if not endpoint_url:
        await message.reply_text('لطفا Endpoint را به صورت لینک وارد کنید.', reply_markup=build_back_keyboard())
        return

    pending = _PENDING_S3.get(user_id, {})
    access_key = pending.get("access_key") or await model_async.get_access_key(user_id)
    secret_key = pending.get("secret_key") or await model_async.get_secret_key(user_id)

    if not access_key or not secret_key:
        _PENDING_S3.pop(user_id, None)
        await model_async.set_state(user_id, 'home')
        await message.reply_text('اطلاعات ناقص است. لطفاً مجدداً از منوی تنظیم S3 اقدام فرمایید.', reply_markup=build_back_keyboard())
        return

    valid_s3 = await s3_service.verify_credentials(
        access_key=access_key,
        secret_key=secret_key,
        endpoint_url=endpoint_url,
        user_id=user_id
    )
    if not valid_s3:
        _PENDING_S3.pop(user_id, None)
        await model_async.set_state(user_id, 'home')
        await message.reply_text(
            'مشخصات S3 نامعتبر است یا باکت یافت نشد. لطفاً ابتدا از صحت کلیدها و وجود باکت در پنل ابری اطمینان حاصل کنید.',
            reply_markup=build_back_keyboard()
        )
        return

    _PENDING_S3.pop(user_id, None)

    # Check captcha if config captcha is enabled (and user not admin)
    is_admin = await model_async.check_admin(user_id)
    if not is_admin and model_async.is_captcha_config_enabled():
        _PENDING_CONFIG[user_id] = {
            "type": "s3",
            "access_key": access_key,
            "secret_key": secret_key,
            "endpoint": endpoint_url,
        }
        from handlers.handler_helpers.message_helpers.captcha_handler import issue_captcha
        await issue_captcha(message, user_id, "config_s3")
        return

    await model_async.set_access_key(user_id, access_key)
    await model_async.set_secret_key(user_id, secret_key)
    await model_async.set_s3_endpoint(user_id, endpoint_url)
    await model_async.set_state(user_id, 'home')
    await message.reply_text(
        'اطلاعات S3 با موفقیت ذخیره شد.',
        reply_markup=build_back_keyboard()
    )