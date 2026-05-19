from pyrogram.types import Message
from db.model_acync import set_state, check_admin, verify_check
from config import START_TXT, HELP_TXT
from utils.keyboards import build_start_keyboard, build_back_keyboard, build_management_keyboard, build_back_management_keyboard
from db.db_sync import DB_NAME
from db.model_acync import add_user, is_user_exist





async def back(message:Message, user_id):
        await set_state(user_id,'home')
        is_admin = await check_admin(user_id)
        await message.edit_text(
            START_TXT,
            reply_markup=build_start_keyboard(is_admin)
        )

async def set_bale_id(message:Message, user_id):
        await set_state(user_id,'enter_bale_id')
        is_verify = await verify_check(user_id)
        is_admin = await check_admin(user_id)
        if is_verify:
            await message.edit_text(
                'شما قبلا احراز هویت شده اید.',
                reply_markup=build_start_keyboard(is_admin)
            )
        else:
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

async def start(message:Message, user_id):
    if await is_user_exist(user_id) == False:
        await add_user(user_id)
    is_admin = await check_admin(user_id)
    await message.reply_text(
        START_TXT,
        reply_markup=build_start_keyboard(is_admin)
    )

async def ban_bale(message:Message, user_id):
    is_admin = await check_admin(user_id)
    if is_admin:
        await set_state(user_id,'enter_bale_ban')
        await message.reply_text(
             "لطفا ID عددی بله کسی را که می خواهید بن کنید را وارد نمایید.",
             reply_markup=build_back_management_keyboard()
        )


async def unban_bale(message:Message, user_id):
    is_admin = await check_admin(user_id)
    if is_admin:
        await set_state(user_id, 'enter_bale_unban')
        await message.reply_text(
             'لطفا ID عددی بله کسی را که می خواهید آنبن کنید را وارد کنید.',
             reply_markup=build_back_management_keyboard()
        )