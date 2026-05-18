from pyrogram.types import Message
from db.model_acync import set_state, check_admin
from config import START_TXT, HELP_TXT
from utils.keyboards import build_start_keyboard, build_back_keyboard, build_management_keyboard
from db.db_sync import DB_NAME






async def back(message:Message, user_id):
        await set_state(user_id,'home')
        is_admin = await check_admin(user_id)
        await message.edit_text(
            START_TXT,
            reply_markup=build_start_keyboard(is_admin)
        )

async def set_bale_id(message:Message, user_id):
        await set_state(user_id,'enter_bale_id')
        await message.edit_text(
            'لطفا ID عددی بله خود را وارد کنید:',
            reply_markup=build_back_keyboard()
        )

async def help(message:Message, user_id):
        await set_state(user_id,'home')
        is_admin = await check_admin(user_id)
        await message.edit_text(
            START_TXT,
            reply_markup=build_start_keyboard(is_admin)
        )

async def management(message:Message, user_id):
        is_admin = await check_admin(user_id)
        if is_admin:
            await set_state(user_id,'management')
            await message.edit_text(
                "ادمین عزیز به پنل مدیریت ربات خوش آمدید",
                reply_markup=build_management_keyboard()
            )

async def back_to_management(message: Message, user_id):
       is_admin = await check_admin(user_id)
       if is_admin:
            await set_state(user_id,'management')
            await message.edit_text(
                "ادمین عزیز به پنل مدیریت ربات خوش آمدید",
                reply_markup=build_management_keyboard()
            )


async def get_db(message: Message, user_id):
    is_admin = await check_admin(user_id)
    if is_admin:
        await message.reply_document(
                document=DB_NAME
            )
        await message.reply_text(
                "ادمین عزیز به پنل مدیریت ربات خوش آمدید",
                reply_markup=build_management_keyboard()
            )


async def send_support_message(message:Message, user_id):
      await set_state(user_id,"send_support_message")
      await message.edit_text(
            'لطفا پیام خود را وارد کنید:',
            reply_markup=build_back_keyboard()
      )
