import json
import secrets
import os
import time
import aiohttp
from threading import Lock
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message

# Load config
with open("config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)

TEL_API_ID = cfg["TELEGRAM"]["API_ID"]
TEL_API_HASH = cfg["TELEGRAM"]["API_HASH"]
TEL_BOT_TOKEN = cfg["TELEGRAM"]["TOKEN_BOT"]
BALE_BOT_TOKEN = cfg["BALE"]['TOKEN_BOT']

ADMIN_ID = cfg["TELEGRAM"]['ADMIN_ID']

plugins = dict(root="plugins")

USERS_FILE = "users.json"
_users_lock = Lock()

users = []

def load_users():
    global users
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    users = data
                else:
                    users = []
        except Exception:
            users = []
    else:
        users = []

def save_users():
    with _users_lock:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)

load_users()

telapp = Client(
    "bot",
    api_id=TEL_API_ID,
    api_hash=TEL_API_HASH,
    bot_token=TEL_BOT_TOKEN,
    proxy=dict(scheme="socks5", hostname="127.0.0.1", port=10808),
)
#------------------------------------------------------------------------------------------BALE Handle-----------------------------------------------------------------
async def send_verify_code(chat_id: int, code: str):
    url = f"https://tapi.bale.ai/bot{BALE_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": f"کد تایید شما: {code}"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            data = await resp.json()

            if not data.get("ok"):
                raise Exception(
                    f"Bale API Error {data.get('error_code')}: {data.get('description')}"
                )

            return data["result"]


async def send_file(chat_id:int,url:str):
    pass



#------------------------------------------------------------------------------------------TELEGRAM Handle-------------------------------------------------------------
start_txt = "در اینجا باید مطلب شروع قرار گیرد"
help_txt = "helptext"



def find_user(tg_id: int):
    for u in users:
        if u["tg_id"] == tg_id:
            return u
    return None


def generate_verify_code() -> str:
    """ساخت کد فعال‌سازی ۵ رقمی"""
    return str(secrets.randbelow(90000) + 10000)


def can_send_verify_code(user: dict) -> tuple[bool, str]:
    """
    بررسی می‌کند آیا امکان ارسال کد فعال‌سازی برای کاربر وجود دارد یا خیر.

    خروجی:
        (True, message)  -> مجاز به ارسال
        (False, message) -> غیرمجاز
    """

    now = int(time.time())

    # بررسی بلاک دائمی توسط ادمین
    if user.get("is_blocked", False):
        return False, "شما توسط ادمین بن شده اید."

    # بررسی cooldown
    cooldown_until = user["cooldown_until"]
    if cooldown_until > now:
        remaining = cooldown_until - now
        return False, f"{remaining} ثانیه دیگر تلاش کنید."

    # بررسی تعداد تلاش‌ها
    send_attempts = user["send_attempts"]
    max_attempts = 3

    if send_attempts >= max_attempts:
        # فعال کردن cooldown جدید (10 دقیقه)
        user["cooldown_until"] = now + 600
        user["send_attempts"] = 0  # ریست تلاش‌ها بعد از ورود به cooldown
        return False, "تعداد تلاش مجاز تمام شده است. شما به مدت 10 دقیقه محدود شدید."
    user["send_attempts"] += 1

    return True, "امکان ارسال کد وجود دارد."






# ---------- keyboards ----------
def build_start_keyboard(user_id):
    rows = [
        [
            InlineKeyboardButton(text="تنظیم ID عددی بله", callback_data='set_bale_id'),
        ],
        [InlineKeyboardButton(text='حمایت مالی', url='https://google.com')],
        [InlineKeyboardButton(text='راهنمای استفاده از ربات', callback_data='help')],
    ]

    if user_id == ADMIN_ID:
        rows.append([InlineKeyboardButton(text='پنل ادمینی', callback_data='management')])

    return InlineKeyboardMarkup(rows)



def build_back_keyboard():
    rows = [
        [
            InlineKeyboardButton(text='بازگشت', callback_data='back')
        ]
    ]
    return InlineKeyboardMarkup(rows)



def build_back_2_management_keyboard():
    rows = [
        [
            InlineKeyboardButton(text='بازگشت', callback_data='back_to_management')
        ]
    ]
    return InlineKeyboardMarkup(rows)





def build_management_keyboard():
    rows = [
        [
            InlineKeyboardButton(text='دریافت فایل users.json',callback_data='get_user_json')
        ],
        [
            InlineKeyboardButton(text='مسدود کردن کاربر بر اساس ID عددی بله',callback_data='ban_bale_id'),
            InlineKeyboardButton(text='مسدود کردن کاربر بر اساس ID عددی تلگرام',callback_data='ban_telegram_id'),
        ],
        [
            InlineKeyboardButton(text='نمایش 10 کاربر پر مصرف', callback_data='show_10_high')
        ],
        [
            InlineKeyboardButton(text='مشاهده پیام های بخش پشتیبانی', callback_data='show_support_messages')
        ],
        [
            InlineKeyboardButton(text='بازگشت', callback_data='back')
        ]
    ]
    return InlineKeyboardMarkup(rows)



# ---------- start ----------
@telapp.on_message(filters.command('start') & filters.private)
async def start_command_handle(client: Client, message: Message):
    user_id = int(message.from_user.id)

    user = find_user(user_id)

    if not user:
        user = {
            "tg_id": user_id,
            "bale_id": 0,
            'is_verified': False,
            'verify_code': '',
            'verify_code_expire':0,
            "user_step": 'home',
            'cooldown_until': 0,
            'verify_attempts':0,
            'send_attempts':0,
            'downloaded_volume': 0,
            'is_blocked':False,
            'created_at':0
        }
        users.append(user)
        save_users()
    user['user_step'] = 'home'
    await message.reply_text(
        start_txt,
        reply_markup=build_start_keyboard(user_id)
    )











# ---------- callbacks ----------
@telapp.on_callback_query()
async def callback_handler(client: Client, callback: CallbackQuery):
    user_id = int(callback.from_user.id)
    user = find_user(user_id)

    if not user:
        await callback.answer("کاربر یافت نشد", show_alert=True)
        return


    if callback.data == 'back':
        user['user_step'] = 'home'
        await callback.message.edit_text(
            start_txt,
            reply_markup=build_start_keyboard(user_id)
        )
        return



    if callback.data == 'set_bale_id':
        user['user_step'] = 'enter_bale_id'
        await callback.message.edit_text(
            'لطفا ID عددی بله خود را وارد کنید:',
            reply_markup=build_back_keyboard()
        )


    if callback.data == 'help':
        user["user_step"] = 'home'
        await callback.message.edit_text(
            help_txt,
            reply_markup=build_start_keyboard(user_id)
        )

    if callback.data == 'management':
        if user_id == ADMIN_ID:
            await callback.message.edit_text(
                "ادمین عزیز به پنل مدیریت ربات خوش آمدید",
                reply_markup=build_management_keyboard()
            )
    
    if callback.data == 'back_to_management':
        if user_id == ADMIN_ID:
            await callback.message.edit_text(
                "ادمین عزیز به پنل مدیریت ربات خوش آمدید",
                reply_markup=build_management_keyboard()
            )

    if callback.data == 'get_user_json':
        if user_id == ADMIN_ID:
            await callback.message.reply_document(
                document='users.json'
            )
    
    if callback.data == 'ban_bale_id':
        if user_id == ADMIN_ID:
            user['user_step'] = 'enter_ban_bale_id'
            await callback.message.edit_text(
                'لطفا ID عدد کسی را که می خواهید Ban کنید وارد کنید.'
            )

    save_users()













#---------- دریافت ورودی ----------

@telapp.on_message(filters.private & filters.text)
async def handle_input(client: Client, message: Message):
    user_id = int(message.from_user.id)
    user = find_user(user_id)

    if not user or not user.get("user_step"):
        return

    if user['user_step'] == 'enter_bale_id': 
        if not message.text.isdigit():
            await message.reply_text("لطفا فقط شناسه عددی ارسال کنید.")
            return
        id_num = int(message.text)
        can_send_verify, msg = can_send_verify_code(user)
        if can_send_verify:
            random_code = generate_verify_code()
            user["verify_code"] = random_code
            user['user_step'] = 'waiting_verification_code'
            await send_verify_code(id_num, random_code)
            user["bale_id"] = id_num
            user["verify_code_expire"] = int(time.time()) + 300
            await message.reply_text(
                "کد فعال سازی به بله شما ارسال شد لطفا کد را وارد کنید.",
                reply_markup=build_back_keyboard()
            )
        else:
            await message.reply_text(
                msg,
                reply_markup=build_back_keyboard()
            )

    elif user['user_step'] == "waiting_verification_code":
        if time.time() < user["verify_code_expire"]:
            if user['verify_code'] == message.text:
                user['is_verified'] = True
                user["verify_code"] = ""
                user["verify_code_expire"] = 0
                user["verify_attempts"] = 0
                user["send_attempts"] = 0
                user["verify_attempts"] = 0 
                user['created_at'] = int(time.time())
                user['user_step'] = 'home'
                await message.reply_text(
                    'اکانت بله شما با موفقیت ثبت شد.',
                    reply_markup=build_start_keyboard(user_id)
                )
                save_users()
            else:
                now = int(time.time())
                verify_attempts = user["verify_attempts"]
                max_attempts = 3
                if verify_attempts >= max_attempts:
                    user["cooldown_until"] = now + 600
                    user["verify_attempts"] = 0  # ریست تلاش‌ها بعد از ورود به cooldown
                    await message.reply_text(
                        "تعداد تلاش مجاز تمام شده است. شما به مدت 10 دقیقه محدود شدید.",
                        reply_markup=build_back_keyboard()
                    )
                else:
                    user["verify_attempts"] += 1
                    await message.reply_text(
                        'کد فعال سازی را اشتباه وارد کرده اید.'
                    )
        else:
            user['user_step'] = 'home'
            await message.reply_text(
                'کد فعال سازی منقضی شده است دوباره تلاش کنید.',
                reply_markup=build_start_keyboard(user_id=user_id)
            )

    if user['user_step'] == 'enter_ban_bale_id':
        if user_id != ADMIN_ID:
            return

        if not message.text.isdigit():
            await message.reply_text("فقط عدد وارد کنید")
            return

        id_num = int(message.text)
        for i in users:
            if i['bale_id'] == id_num:
                i['is_blocked'] = True
                await message.reply_text(
                    'کاربر با خاک یکسان شد.',
                    reply_markup=build_back_2_management_keyboard()
                )
                save_users()
                return
        await message.reply_text(
            'کاربر یافت نشد.',
            reply_markup=build_back_2_management_keyboard()
        )


telapp.run()