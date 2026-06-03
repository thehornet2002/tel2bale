# 🚀 TEL2BALE — ربات انتقال پیام از تلگرام به بله

<div align="center">

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen)](https://github.com/thehornet2002/tel2bale)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**Telegram to Bale Bridge Bot**

</div>

---

## 📌 معرفی پروژه

**TEL2BALE** یک ربات واسط است که پیام‌های کاربران را از تلگرام دریافت می‌کند و آن‌ها را به پیام‌رسان **بله** منتقل می‌کند.

این پروژه مخصوص شرایطی طراحی شده که دسترسی به تلگرام سخت، کند یا محدود است؛ کاربر پیام، فایل یا رسانه را در تلگرام برای ربات می‌فرستد و ربات آن را به مقصد تنظیم‌شده در بله ارسال می‌کند.

رفتار انتقال فایل‌ها:

- فایل‌های کوچک‌تر یا مساوی مقدار `TEL_MAX_FILE_SIZE` به‌صورت مستقیم به بله ارسال می‌شوند.
- فایل‌های بزرگ‌تر از این مقدار ابتدا روی **Arvan Storage** آپلود می‌شوند و لینک موقت آن برای مقصد ارسال می‌شود.
- مصرف حجم کاربران از طریق سیستم quota کنترل می‌شود.
- برای جلوگیری از race condition، ثبت مصرف حجم به‌صورت atomic انجام می‌شود.

---

## ✨ قابلیت‌ها

- انتقال پیام متنی از تلگرام به بله
- انتقال عکس، ویدئو، صوت، voice، document، animation، location و contact
- پشتیبانی از فایل‌های بزرگ با Arvan Storage
- تنظیم شناسه عددی بله توسط هر کاربر
- تنظیم Bot Token بله توسط هر کاربر
- تنظیم Access Key و Secret Key آروان توسط کاربر
- پنل مدیریت با دکمه‌های inline
- مدیریت ادمین‌ها
- بن و آنبن کاربران با Telegram ID یا Bale ID
- مشاهده ۱۰ کاربر پرمصرف
- تنظیم محدودیت مصرف برای همه یا برای یک کاربر خاص
- ارسال پیام همگانی
- ارسال پیام به کاربر خاص
- دریافت فایل دیتابیس
- دریافت و مشاهده پیام‌های پشتیبانی
- Join اجباری برای کانال‌های تلگرام
- پشتیبانی Join اجباری از فرمت‌های مختلف کانال:
  - `@channel`
  - `channel`
  - `https://t.me/channel`
  - `t.me/channel`
  - آیدی عددی مثل `-1001234567890`
- ذخیره‌سازی اطلاعات با SQLite
- لاگ‌گیری چرخشی در پوشه `logs/`

---

## 📋 پیش‌نیازها

### سیستم‌عامل پیشنهادی

- Ubuntu 20.04+
- Debian 11+
- یا هر سرور Linux سازگار با Python 3.10+

### منابع پیشنهادی

- RAM: حداقل 512MB
- Disk: حداقل 1GB فضای آزاد
- Python: نسخه 3.10 یا بالاتر

### سرویس‌ها و توکن‌های لازم

#### 1. Telegram Bot Token

از [@BotFather](https://t.me/BotFather) یک ربات بسازید و توکن آن را دریافت کنید.

#### 2. Telegram API ID و API Hash

از سایت [my.telegram.org](https://my.telegram.org) وارد بخش **API development tools** شوید و مقدارهای زیر را دریافت کنید:

- `TEL_API_ID`
- `TEL_API_HASH`

#### 3. Bale Bot Token

در پیام‌رسان بله، از BotFather بله یک ربات بسازید و توکن آن را دریافت کنید.

#### 4. Arvan Storage

برای انتقال فایل‌های بزرگ، هر کاربر باید Access Key و Secret Key مربوط به Arvan Storage خودش را در ربات ثبت کند.

---

## 🚀 نصب و راه‌اندازی

## روش ۱: نصب خودکار

```bash
sudo bash <(curl -Ls https://raw.githubusercontent.com/thehornet2002/tel2bale/main/setup.sh)
```

اسکریپت نصب خودکار این کارها را انجام می‌دهد:

1. نصب ابزارهای لازم سیستم
2. دانلود آخرین release پروژه
3. نصب Python و venv
4. ساخت virtual environment
5. نصب dependencyهای Python
6. ساخت فایل `.env`
7. ساخت و فعال‌سازی سرویس systemd

---

## روش ۲: نصب دستی

```bash
git clone https://github.com/thehornet2002/tel2bale.git
cd tel2bale

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

cp example.env .env
nano .env

python main.py
```

در ویندوز:

```powershell
python -m venv .venv
.\.venv\Scripts\activate

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

copy example.env .env
python main.py
```

---

## ⚙️ تنظیمات `.env`

نمونه فایل تنظیمات:

```env
# Telegram Config
TEL_API_ID=123456
TEL_API_HASH=your_telegram_api_hash
TEL_BOT_TOKEN=your_telegram_bot_token
TEL_ADMIN_IDS=123456789,987654321

TEL_START_TXT=به ربات انتقال پیام تلگرام به بله خوش آمدید.
TEL_HELP_TXT=ابتدا شناسه بله و توکن ربات بله خود را تنظیم کنید، سپس پیام‌ها را ارسال کنید.

TEL_ADS_CHANNELS=
TEL_MAX_FILE_SIZE=20
TEL_IN_MEMORY=False

# Telegram Proxy Config
TEL_PROXY_SCHEME=
TEL_PROXY_HOST=
TEL_PROXY_PORT=
```

### توضیح متغیرها

| متغیر | توضیح |
|---|---|
| `TEL_API_ID` | API ID تلگرام |
| `TEL_API_HASH` | API Hash تلگرام |
| `TEL_BOT_TOKEN` | توکن ربات تلگرام |
| `TEL_ADMIN_IDS` | آیدی عددی ادمین‌ها، جداشده با کاما |
| `TEL_START_TXT` | متن پیام شروع |
| `TEL_HELP_TXT` | متن راهنما |
| `TEL_ADS_CHANNELS` | لیست کانال‌های Join اجباری، جداشده با کاما |
| `TEL_MAX_FILE_SIZE` | سقف ارسال مستقیم فایل به مگابایت |
| `TEL_IN_MEMORY` | اگر `True` باشد فایل‌های کوچک در RAM نگهداری می‌شوند |
| `TEL_PROXY_SCHEME` | نوع پروکسی تلگرام، مثل `socks5` |
| `TEL_PROXY_HOST` | آدرس پروکسی |
| `TEL_PROXY_PORT` | پورت پروکسی |

---

## 📂 ساختار پروژه

```text
tel2bale/
├── main.py
├── config.py
├── requirements.txt
├── setup.sh
├── example.env
├── .env
│
├── db/
│   ├── db_async.py
│   ├── db_sync.py
│   ├── model_async.py
│   └── model_sync.py
│
├── handlers/
│   ├── commands.py
│   ├── messages.py
│   ├── callback.py
│   └── handler_helpers/
│       ├── command_helper.py
│       ├── message_helper.py
│       └── callback_helper.py
│
├── services/
│   ├── arvan_service.py
│   ├── bale_service.py
│   └── quota_service.py
│
├── utils/
│   ├── filters.py
│   ├── keyboards.py
│   └── logger.py
│
└── logs/
    └── bot.log
```

> نکته: نام پوشه handlers باید دقیقاً `handlers` باشد، چون پلاگین‌ها از همین مسیر لود می‌شوند.

---

## 🔄 جریان کلی عملکرد

```text
کاربر در تلگرام پیام می‌فرستد
        │
        ▼
handlers/messages.py
        │
        ▼
بررسی state کاربر
        │
        ├── اگر کاربر در فرم تنظیمات باشد → پردازش ورودی فرم
        │
        └── اگر state برابر home باشد → انتقال پیام به بله
                │
                ▼
        بررسی Bale ID و Bot Token
                │
                ▼
        بررسی نوع پیام و حجم فایل
                │
        ┌───────┴────────┐
        │                │
  فایل کوچک         فایل بزرگ
        │                │
        ▼                ▼
ارسال مستقیم      آپلود در Arvan Storage
به Bale API       و ارسال لینک موقت
        │                │
        └───────┬────────┘
                ▼
        ثبت مصرف quota در SQLite
```

---

## 🎮 نحوه استفاده کاربران

1. دستور `/start` را در ربات تلگرام بزنید.
2. از منو، گزینه **تنظیم ID عددی بله** را انتخاب کنید.
3. شناسه عددی بله مقصد را وارد کنید.
4. گزینه **تنظیم Bot Token بله** را انتخاب کنید.
5. توکن ربات بله خود را وارد کنید.
6. برای فایل‌های بزرگ، گزینه **تنظیم Access Key و Secret Key فضای ابری آروان** را انتخاب کنید.
7. حالا هر پیام یا فایل پشتیبانی‌شده‌ای را به ربات تلگرام بفرستید تا به بله منتقل شود.

---

## 🛠️ امکانات پنل مدیریت

ادمین‌ها از منوی مدیریت می‌توانند این کارها را انجام دهند:

- دریافت فایل دیتابیس
- بن با ID بله
- آنبن با ID بله
- بن با ID تلگرام
- آنبن با ID تلگرام
- نمایش ۱۰ کاربر پرمصرف
- مشاهده پیام‌های پشتیبانی
- تنظیم محدودیت مصرف برای همه کاربران
- تنظیم محدودیت مصرف برای یک کاربر
- ایجاد Join اجباری
- حذف Join اجباری
- ارسال تبلیغات یا پیام همگانی
- ارسال پیام به فرد خاص
- اضافه کردن ادمین
- حذف ادمین
- تنظیم عکس پروفایل ربات

---

## 📢 Join اجباری

برای اضافه‌کردن کانال Join اجباری، ادمین می‌تواند یکی از این فرمت‌ها را وارد کند:

```text
@my_channel
my_channel
https://t.me/my_channel
t.me/my_channel
-1001234567890
```

قبل از ذخیره کانال، ربات بررسی می‌کند:

1. ورودی معتبر باشد.
2. کانال وجود داشته باشد.
3. ربات در کانال عضو باشد.
4. ربات امکان بررسی عضویت کاربران را داشته باشد.

> برای کانال‌های عمومی، استفاده از username یا لینک عمومی بهتر است.  
> برای کانال‌های خصوصی، معمولاً باید از آیدی عددی `-100...` استفاده شود.  
> اگر ربات نتواند عضویت کاربران را بررسی کند، بهتر است ربات را در کانال admin کنید.

---

## 📦 فایل‌های بزرگ و Arvan Storage

اگر حجم فایل از مقدار `TEL_MAX_FILE_SIZE` بیشتر باشد:

1. فایل از تلگرام دانلود می‌شود.
2. با Access Key و Secret Key کاربر به Arvan Storage آپلود می‌شود.
3. لینک موقت ساخته می‌شود.
4. لینک برای مقصد در بله ارسال می‌شود.
5. فایل موقت از سرور حذف می‌شود.

---

## 📊 سیستم quota

هر کاربر می‌تواند محدودیت مصرف داشته باشد.

- مقدار `0` یعنی بدون محدودیت.
- مقدار مصرف‌شده در جدول `users` و ستون `downloaded_volume` ذخیره می‌شود.
- محدودیت کاربر در ستون `limit_download` ذخیره می‌شود.
- بررسی و رزرو quota به‌صورت atomic انجام می‌شود تا ارسال همزمان چند فایل باعث عبور از سقف مجاز نشود.
- در صورت شکست ارسال یا آپلود، quota رزروشده rollback می‌شود.

---

## 🗄️ دیتابیس

پروژه از SQLite استفاده می‌کند و فایل دیتابیس به‌صورت پیش‌فرض این است:

```text
bot.db
```

جداول اصلی:

### `users`

اطلاعات کاربران، وضعیت ban/admin، شناسه بله، توکن بله، کلیدهای آروان، state و مصرف حجم.

### `support_messages`

پیام‌های پشتیبانی ارسال‌شده توسط کاربران.

برای مشاهده دیتابیس می‌توانید از ابزارهایی مثل `sqlite3` یا DB Browser for SQLite استفاده کنید.

نمونه:

```bash
sqlite3 bot.db
```

```sql
SELECT telegram_id, bale_id, downloaded_volume, limit_download
FROM users
ORDER BY downloaded_volume DESC
LIMIT 10;
```

---

## 📝 لاگ‌ها

لاگ‌های پروژه در مسیر زیر ذخیره می‌شوند:

```text
logs/bot.log
```

در نصب systemd می‌توانید لاگ‌ها را با این دستور ببینید:

```bash
sudo journalctl -u Tel2Bale -f
```

---

## 🔧 مدیریت سرویس systemd

```bash
sudo systemctl status Tel2Bale
sudo systemctl start Tel2Bale
sudo systemctl stop Tel2Bale
sudo systemctl restart Tel2Bale
sudo systemctl enable Tel2Bale
```

مشاهده لاگ زنده:

```bash
sudo journalctl -u Tel2Bale -f
```

مشاهده ۵۰ خط آخر:

```bash
sudo journalctl -u Tel2Bale -n 50
```

---

## 🐛 رفع خطاهای رایج

### ربات بالا نمی‌آید

```bash
sudo journalctl -u Tel2Bale -n 50
```

موارد زیر را بررسی کنید:

- مقدارهای `.env` درست باشند.
- نام پوشه `handlers` درست باشد.
- dependencyها نصب شده باشند.
- فایل `bot.db` قابل ساختن باشد.
- توکن تلگرام معتبر باشد.

---

### خطای `ModuleNotFoundError: No module named 'handlers'`

نام پوشه باید `handlers` باشد، نه `handler`.

```bash
mv handler handlers
touch handlers/__init__.py
touch handlers/handler_helpers/__init__.py
```

---

### فایل‌ها به بله ارسال نمی‌شوند

بررسی کنید:

- Bale ID کاربر تنظیم شده باشد.
- Bot Token بله تنظیم شده باشد.
- ربات بله امکان ارسال پیام به مقصد را داشته باشد.
- حجم فایل از quota کاربر عبور نکرده باشد.
- برای فایل‌های بزرگ، کلیدهای Arvan Storage تنظیم شده باشند.

---

### Join اجباری کار نمی‌کند

بررسی کنید:

- کانال عمومی باشد یا آیدی عددی معتبر داشته باشد.
- ربات در کانال عضو باشد.
- برای بررسی عضویت، بهتر است ربات در کانال admin باشد.
- مقدار ذخیره‌شده در `TEL_ADS_CHANNELS` معتبر باشد.

---

### خطای نصب dependencyها

```bash
sudo apt update
sudo apt install -y build-essential python3-dev python3-venv
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

---

## 🔐 نکات امنیتی

- فایل `.env` را در Git منتشر نکنید.
- توکن‌های تلگرام و بله را در لاگ یا پیام عمومی قرار ندهید.
- Access Key و Secret Key آروان را فقط برای کاربر مربوطه نگهداری کنید.
- دسترسی فایل دیتابیس و `.env` را محدود کنید.
- اگر توکن لو رفت، سریعاً آن را revoke و مجدداً صادر کنید.
- برای سیستم production، از کاربر جداگانه systemd به‌جای `root` استفاده کنید.

---

## 📌 نکات توسعه

### ثبت commandهای ربات

برای نمایش commandها در منوی تلگرام، در زمان راه‌اندازی می‌توانید commandهای زیر را ثبت کنید:

```python
from pyrogram.types import BotCommand

await telapp.set_bot_commands([
    BotCommand("start", "شروع ربات"),
    BotCommand("help", "راهنمای استفاده از ربات"),
])
```

در نسخه‌هایی از Kurigram که `telapp.run(main())` را پشتیبانی نمی‌کنند، از `asyncio.run(main())` استفاده کنید.

---

## ✅ برنامه‌های آینده

- [ ] تنظیم endpoint دلخواه برای S3-compatible storage
- [ ] بهبود مدیریت bucket در Arvan Storage
- [ ] افزودن گروه پشتیبانی به‌جای ذخیره پیام در دیتابیس
- [ ] محدودیت تعداد کاربران فعال
- [ ] پنل بهتر برای مدیریت پیام‌های پشتیبانی
- [ ] تست خودکار برای quota و state machine

---

## 🤝 مشارکت

برای مشارکت:

1. پروژه را Fork کنید.
2. یک branch جدید بسازید.
3. تغییرات را commit کنید.
4. Pull Request ارسال کنید.

```bash
git checkout -b feature/my-feature
git commit -m "Add my feature"
git push origin feature/my-feature
```

---

## 📞 پشتیبانی

- Issues: [GitHub Issues](https://github.com/thehornet2002/tel2bale/issues)
- Telegram: [@thehornet2002](https://t.me/thehornet2002)

---

## 📜 License

این پروژه تحت لایسنس MIT منتشر شده است.

---

## ❤️ حمایت مالی ❤️

حمایت مالی [دارمت](https://daramet.com/Hornet2002)

---
<div align="center">

اگر این پروژه برایتان مفید بود، ⭐ دادن به مخزن باعث دلگرمی است.

</div>
