from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton



def build_start_keyboard(is_admin):
    rows = [
        [
            InlineKeyboardButton(text="تنظیم ID عددی بله", callback_data='set_bale_id')],
        [InlineKeyboardButton(text='حمایت مالی', url='https://google.com')],
        [InlineKeyboardButton(text='راهنمای استفاده از ربات', callback_data='help')],
        [InlineKeyboardButton(text="ارسال پیام به پشتیبانی", callback_data='send_support_message'),]
    ]

    if is_admin:
        rows.append([InlineKeyboardButton(text='پنل مدیریت', callback_data='management')])

    return InlineKeyboardMarkup(rows)



def build_back_keyboard():
    rows = [
        [
            InlineKeyboardButton(text='بازگشت', callback_data='back')
        ]
    ]
    return InlineKeyboardMarkup(rows)



def build_back_management_keyboard():
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