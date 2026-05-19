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
            InlineKeyboardButton(text='دریافت فایل دیتابیس',callback_data='get_db')
        ],
        [
            InlineKeyboardButton(text='بن با ID بله',callback_data='ban_bale_id'),
            InlineKeyboardButton(text='آنبن با ID بله',callback_data='unban_bale_id'),
        ],
        [
            InlineKeyboardButton(text='بن با ID تلگرام',callback_data='ban_telegram_id'),
            InlineKeyboardButton(text='آنبن با ID تلگرام',callback_data='unban_telegram_id'),
        ],
        [
            InlineKeyboardButton(text='نمایش 10 کاربر پر مصرف', callback_data='show_10_high')
        ],
        [
            InlineKeyboardButton(text='مشاهده پیام های بخش پشتیبانی', callback_data='show_support_messages')
        ],
        [
            InlineKeyboardButton(text='تنظیم محدودیت روزانه',callback_data='set_daily_limit'),
            InlineKeyboardButton(text='تنظبم محدودیت کلی',callback_data='set_limit'),
        ],
        [
            InlineKeyboardButton(text='ایجاد Join اجباری',callback_data='set_join_ads'),
            InlineKeyboardButton(text='حذف Join اجباری',callback_data='delete_join_ads'),
        ],
        [
            InlineKeyboardButton(text='ارسال تبلیغات',callback_data='send_ads'),
            InlineKeyboardButton(text='ارسال پیام به فرد خاص', callback_data='send_message')
        ],
        [
            InlineKeyboardButton(text="اضافه کردن ادمین", callback_data='add_admin'),
            InlineKeyboardButton(text='حذف ادمین', callback_data='delete_admin')
        ],
        [
            InlineKeyboardButton(text='بازگشت', callback_data='back')
        ]
    ]
    return InlineKeyboardMarkup(rows)



def build_ads_channels(channels: list):
    rows = []
    for i in range(len(channels)):
        rows.append(
            [InlineKeyboardButton(text=f"کانال {i+1}", url=f"https://t.me/{channels[i]}")]
        )
    rows.append([InlineKeyboardButton(text="عضو شدم", callback_data='start')])
    return InlineKeyboardMarkup(rows)