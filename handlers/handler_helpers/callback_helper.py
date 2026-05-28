from pyrogram.types import Message
from db.model_async import set_state, check_admin, verify_check
from config import START_TXT, HELP_TXT
from utils.keyboards import build_start_keyboard, build_back_keyboard, build_management_keyboard, build_back_management_keyboard, support_keyboard
from db.db_sync import DB_NAME
from db.model_async import add_user, is_user_exist, get_top_users, get_unread_support_message
from config import ADS_CHANNELS, ADMIN_IDS




async def back(message:Message, user_id):
    await set_state(user_id,'home')
    is_admin = await check_admin(user_id)
    await message.edit_text(
        START_TXT,
        reply_markup=build_start_keyboard(is_admin)
    )

async def set_bale_id(message:Message, user_id):
    is_verify = await verify_check(user_id)
    is_admin = await check_admin(user_id)
    if is_verify:
        await set_state(user_id, 'home')
        await message.edit_text(
            'شما قبلا احراز هویت شده اید.',
            reply_markup=build_start_keyboard(is_admin)
        )
    else:
        await set_state(user_id, 'enter_bale_id')
        await message.edit_text(
            'لطفا ID عددی بله خود را وارد کنید:',
            reply_markup=build_back_keyboard()
        )

async def help(message:Message, user_id):
        await set_state(user_id,'home')
        is_admin = await check_admin(user_id)
        await message.edit_text(
            HELP_TXT,
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
    await message.edit_text(
        START_TXT,
        reply_markup=build_start_keyboard(is_admin)
    )

async def ban_bale(message:Message, user_id):
    is_admin = await check_admin(user_id)
    if is_admin:
        await set_state(user_id,'enter_bale_ban')
        await message.edit_text(
             "لطفا ID عددی بله کسی را که می خواهید بن کنید را وارد نمایید.",
             reply_markup=build_back_management_keyboard()
        )


async def unban_bale(message:Message, user_id):
    is_admin = await check_admin(user_id)
    if is_admin:
        await set_state(user_id, 'enter_bale_unban')
        await message.edit_text(
             'لطفا ID عددی بله کسی را که می خواهید آنبن کنید را وارد کنید.',
             reply_markup=build_back_management_keyboard()
        )


async def ban_telegram(message:Message, user_id):
    is_admin = await check_admin(user_id)
    if is_admin:
        await set_state(user_id,'enter_telegram_ban')
        await message.edit_text(
            'لطفا ID عددی تلگرام کسی را که می خواهید بن کنید وارد کنید:',
            reply_markup=build_back_management_keyboard()
        )

async def unban_telegram(message:Message, user_id):
    is_admin = await check_admin(user_id)
    if is_admin:
        await set_state(user_id,'enter_telegram_unban')
        await message.edit_text(
            'لطفا ID عددی تلگرام کسی را که می خواهید آنبن کنید وارد کنید:',
            reply_markup=build_back_management_keyboard()
        )

async def show_10_high(message:Message, user_id):
    is_admin = await check_admin(user_id)
    if is_admin:
        message_txt = """|  Telegram ID  |     Bale ID    |  Downloaded Volume  |\n"""
        list = await get_top_users()
        for i in list:
             message_txt += f"|  {i['tg_id']}  |{i['bale_id']}|                   {i['downloaded_volume']}                   |\n"
        await message.edit_text(
            message_txt,
            reply_markup=build_back_management_keyboard()
        )   
             
async def set_join_ads(message:Message, user_id):
    is_admin = await check_admin(user_id)
    if is_admin:
        await set_state(user_id, 'enter_join_ads_channel')
        await message.edit_text(
            'لطفا ID کانالی که می خواهید اضافه کنید را وارد کنید: (به عنوان مثال tel2bale)',
            reply_markup=build_back_management_keyboard()
        )

async def delete_join_ads(message:Message, user_id):
    is_admin = await check_admin(user_id)
    if is_admin:
        await set_state(user_id, 'enter_delete_join_ads')
        message_txt = 'لطفا ID کانالی که می خواهید حذف کنید را وارد کنید:\n'
        for channel in ADS_CHANNELS:
             message_txt += channel + '\n'
        await message.edit_text(
            message_txt,
            reply_markup=build_back_management_keyboard()
        )

async def send_ads_message(message:Message, user_id):
    is_admin = await check_admin(user_id)
    if is_admin:
        await set_state(user_id,'enter_ads_message')
        await message.edit_text(
             'لطفا پیامی که می خواهید برای همه استفاده کنندگان از ربات بفرستید را وارد نمایید:',
             reply_markup=build_back_management_keyboard()
        )


async def send_message(message:Message, user_id):
    is_admin = await check_admin(user_id)
    if is_admin:
         await set_state(user_id, 'send_message_chat_id')
         await message.edit_text(
              'لطفا ID عددی تلگرام کسی که می خواهید برای آن پیام ارسال کنید را وارد کنید:',
              reply_markup=build_back_management_keyboard()
         )


async def add_admin(message:Message, user_id:int):
    is_admin = await check_admin(user_id)
    if is_admin:
        await set_state(user_id, 'add_admin_send_id')
        await message.edit_text(
             'لطفا ID عددی تلگرام کسی را که می خواهید ادمین کنید را وارد نمایید:'
        )


async def delete_admin(message:Message, user_id:int):
    is_admin = await check_admin(user_id)
    if is_admin:
        await set_state(user_id, 'delete_admin_send_id')
        message_txt = 'لطفا ID ادمینی که می خواهید حذف کنید را وارد کنید:'+ '\n'
        for i in range(len(ADMIN_IDS)):
             message_txt += str(i)+" - " + str(ADMIN_IDS[i]) + '\n'
        await message.edit_text(
            message_txt,
            reply_markup=build_back_management_keyboard()
        )


async def set_profile_photo(message:Message, user_id:int):
    is_admin = await check_admin(user_id)
    if is_admin:
        await set_state(user_id, 'set_profile_photo_send_photo')
        await message.edit_text(
             'لطفا پروفایلی که می خواهید تنظیم کنید را ارسال کنید.',
            reply_markup=build_back_management_keyboard()
        )



async def set_limit_all(message:Message, user_id:int):
    is_admin = await check_admin(user_id)
    if is_admin:
        await set_state(user_id, 'set_limit_all_send_volume')
        await message.edit_text(
            'لطفا میزان محدودیتی که می خواهید اعمال کنید را وارد کنید (به GB):',
            reply_markup=build_back_management_keyboard()
        )


async def set_limit(message:Message, user_id):
    is_admin = await check_admin(user_id)
    if is_admin:
        await set_state(user_id,'set_limit_send_id')
        await message.edit_text(
             'لطفا ID عددی کسی که می خواهید محدودیت برایش اعمال کنید وارد کنید:',
             reply_markup=build_back_management_keyboard()
        )


async def show_support_messages(message:Message, user_id):
    is_admin = await check_admin(user_id)
    if is_admin:
        support_message = await get_unread_support_message()
        if support_message is None:
            await message.reply_text(
                'پیامی وجود ندارد.',
                reply_markup=build_back_management_keyboard()
            )
            return
        m1 = 'پیام ارسال شده از : ' + str(support_message['tg_id'])
        await message.reply_text(
            m1,
        )
        await message.reply_text(
            support_message['message_text'],
            reply_markup=support_keyboard()
        )