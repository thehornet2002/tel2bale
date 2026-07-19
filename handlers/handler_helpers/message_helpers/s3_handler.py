"""
هندلرهای مربوط به تنظیم اطلاعات S3 توسط کاربر.
"""
from pyrogram.types import Message
from db import model_async
from services import s3_service
from utils.keyboards import build_back_keyboard
from utils.parser import validate_link


async def set_s3_access_key(message: Message, user_id: int):
    await model_async.set_access_key(user_id, message.text)
    await model_async.set_state(user_id, 'set_s3_secret_key')
    await message.reply_text('لطفا Secret Key را وارد نمایید.', reply_markup=build_back_keyboard())


async def set_s3_secret_key(message: Message, user_id: int):
    await model_async.set_secret_key(user_id, message.text)
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
    access_key = await model_async.get_access_key(user_id)
    secret_key = await model_async.get_secret_key(user_id)
    valid_s3 = await s3_service.verify_credentials(access_key=access_key, secret_key=secret_key, endpoint_url=endpoint_url)
    if not valid_s3:
        await model_async.set_access_key(user_id, None)
        await model_async.set_secret_key(user_id, None)
        await model_async.set_state(user_id, 'home')
        await message.reply_text(
            'لطفا مشخصات S3 معتبر وارد کنید',
            reply_markup=build_back_keyboard()
        )
        return
    await model_async.set_s3_endpoint(user_id, endpoint_url)
    await model_async.set_state(user_id, 'home')
    await message.reply_text(
        'اطلاعات S3 با موفقیت ذخیره شد.',
        reply_markup=build_back_keyboard()
    )