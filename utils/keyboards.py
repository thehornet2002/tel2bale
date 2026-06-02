from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ButtonStyle


def build_start_keyboard(is_admin):
    rows = [
        [InlineKeyboardButton(text="تنظیم ID عددی بله", callback_data='set_bale_id', style=ButtonStyle('primary'))],
        [InlineKeyboardButton(text='تنظیم Bot Token بله', callback_data='set_bale_bot_token', style=ButtonStyle('primary'))],
        [InlineKeyboardButton(text='تنظیم Access Key و Secret Key فضای ابری آروان', callback_data="set_arvan_storage", style=ButtonStyle('primary'))],
        [InlineKeyboardButton(text='حمایت مالی', url='https://daramet.com/Hornet2002', style=ButtonStyle('success'))],
        [InlineKeyboardButton(text='راهنمای استفاده از ربات', callback_data='help', style=ButtonStyle('success'))],
        [InlineKeyboardButton(text="ارسال پیام به پشتیبانی", callback_data='send_support_message', style=ButtonStyle('success'))]
    ]
    if is_admin:
        rows.append([InlineKeyboardButton(text='پنل مدیریت', callback_data='management', style=ButtonStyle('danger'))])
    return InlineKeyboardMarkup(rows)



def build_back_keyboard():
    rows = [
        [
            InlineKeyboardButton(text='بازگشت', callback_data='back', style=ButtonStyle('success'))
        ]
    ]
    return InlineKeyboardMarkup(rows)



def build_back_management_keyboard():
    rows = [
        [
            InlineKeyboardButton(text='بازگشت', callback_data='back_to_management', style=ButtonStyle('success'))
        ]
    ]
    return InlineKeyboardMarkup(rows)



def build_management_keyboard():
    rows = [
        [
            InlineKeyboardButton(text='دریافت فایل دیتابیس',callback_data='get_db', style=ButtonStyle('primary'))
        ],
        [
            InlineKeyboardButton(text='بن با ID بله',callback_data='ban_bale_id', style=ButtonStyle('danger')),
            InlineKeyboardButton(text='آنبن با ID بله',callback_data='unban_bale_id', style=ButtonStyle('success')),
        ],
        [
            InlineKeyboardButton(text='بن با ID تلگرام',callback_data='ban_telegram_id', style=ButtonStyle('danger')),
            InlineKeyboardButton(text='آنبن با ID تلگرام',callback_data='unban_telegram_id', style=ButtonStyle('success')),
        ],
        [
            InlineKeyboardButton(text='نمایش 10 کاربر پر مصرف', callback_data='show_10_high', style=ButtonStyle('danger')),
            InlineKeyboardButton(text='تنظیم عکس پروفایل ربات', callback_data='set_profile_photo', style=ButtonStyle('primary'))
        ],
        [
            InlineKeyboardButton(text='مشاهده پیام های بخش پشتیبانی', callback_data='show_support_messages', style=ButtonStyle('primary'))
        ],
        [
            InlineKeyboardButton(text='تنظیم محدودیت برای همه',callback_data='set_limit_all', style=ButtonStyle('danger')),
            InlineKeyboardButton(text='تنظیم محدودیت برای یک نفر',callback_data='set_limit', style=ButtonStyle('danger')),
        ],
        [
            InlineKeyboardButton(text='ایجاد Join اجباری',callback_data='set_join_ads', style=ButtonStyle('success')),
            InlineKeyboardButton(text='حذف Join اجباری',callback_data='delete_join_ads', style=ButtonStyle('danger')),
        ],
        [
            InlineKeyboardButton(text='ارسال تبلیغات',callback_data='send_ads', style=ButtonStyle('danger')),
            InlineKeyboardButton(text='ارسال پیام به فرد خاص', callback_data='send_message', style=ButtonStyle('danger'))
        ],
        [
            InlineKeyboardButton(text="اضافه کردن ادمین", callback_data='add_admin', style=ButtonStyle('success')),
            InlineKeyboardButton(text='حذف ادمین', callback_data='delete_admin', style=ButtonStyle('danger'))
        ],
        [
            InlineKeyboardButton(text='بازگشت', callback_data='back', style=ButtonStyle('success'))
        ]
    ]
    return InlineKeyboardMarkup(rows)


def build_ads_channels(channels: list):
    rows = []

    for i, channel in enumerate(channels):
        channel_text = str(channel).strip()

        if channel_text.startswith("http://") or channel_text.startswith("https://"):
            url = channel_text
        elif channel_text.startswith("@"):
            url = f"https://t.me/{channel_text[1:]}"
        elif not channel_text.lstrip("-").isdigit():
            url = f"https://t.me/{channel_text}"
        else:
            url = None

        if url:
            rows.append([
                InlineKeyboardButton(
                    text=f"کانال {i + 1}",
                    url=url
                )
            ])
        else:
            rows.append([
                InlineKeyboardButton(
                    text=f"کانال {i + 1}: {channel_text}",
                    callback_data="noop_ads_channel"
                )
            ])

    rows.append([
        InlineKeyboardButton(
            text="عضو شدم",
            callback_data='start',
            style=ButtonStyle('success')
        )
    ])

    return InlineKeyboardMarkup(rows)

    
def support_keyboard():
    rows = [
        [
            InlineKeyboardButton(text='دریافت پیامی دیگر', callback_data='show_support_messages', style=ButtonStyle('primary')),
            InlineKeyboardButton(text='بازگشت', callback_data='back_to_management', style=ButtonStyle('success'))
        ]
    ]
    return InlineKeyboardMarkup(rows)

def yes_or_no_bale_id():
    rows = [
        [InlineKeyboardButton(text='بله',callback_data='reset_bale_id', style=ButtonStyle('danger'))],
        [InlineKeyboardButton(text='خیر',callback_data='back', style=ButtonStyle('success'))]
    ]
    return InlineKeyboardMarkup(rows)

def yes_or_no_set_arvan():
    rows = [
        [InlineKeyboardButton(text='بله',callback_data='reset_access_key_arvan', style=ButtonStyle('danger'))],
        [InlineKeyboardButton(text='خیر', callback_data='back', style=ButtonStyle('success'))]
    ]
    return InlineKeyboardMarkup(rows)   

def yes_or_no_set_bot_token():
    rows = [
        [InlineKeyboardButton(text='بله',callback_data='reset_bot_token', style=ButtonStyle('danger'))],
        [InlineKeyboardButton(text='خیر', callback_data='back', style=ButtonStyle('success'))]
    ]
    return InlineKeyboardMarkup(rows)   