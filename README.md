# 🚀 TEL2BALE — ربات انتقال پیام از تلگرام به بله

<div align="center">

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen)](https://github.com/thehornet2002/tel2bale)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**Telegram to Bale Bridge Bot**

</div>

---

## 📌 معرفی پروژه

**TEL2BALE** یک ربات پل ارتباطی امن، غیرمسدودکننده و کاملاً Async است که پیام‌ها و فایل‌ها را از تلگرام دریافت کرده و به پیام‌رسان **بله** ارسال می‌کند.

این پروژه مناسب موقعیت‌هایی است که دسترسی مستقیم به تلگرام با محدودیت مواجه است؛ کاربر رسانه‌ها، فایل‌ها یا متن‌های خود را برای ربات تلگرام ارسال می‌کند و ربات با مدیریت خودکار ترافیک، آن را به مقصد مشخص در بله می‌فرستد.

### رفتار انتقال رسانه‌ها:
- فایل‌های زیر مقدار `TEL_MAX_FILE_SIZE` مستقیماً به پیام‌رسان بله ارسال می‌شوند.
- فایل‌های بزرگ‌تر روی **Arvan Storage (سازگار با S3)** آپلود شده و لینک موقت دانلود آن‌ها به بله ارسال می‌شود.
- سهمیه و حجم مصرفی کاربران با سیستم Quota اختصاصی و تراکنش‌های Atomic کنترل می‌شود.
- مدیریت دیتابیس کاملاً غیرمسدودکننده (Async با `aiosqlite`) است و داده‌های پرتکرار در RAM کش می‌شوند.
- مدیریت وضعیت (State) کاربران با اتصال مستقیم به Redis برای پرفورمنس بسیار بالا و بدون درگیری I/O دیسک (همراه با Fallback هوشمند).

---

## ✨ قابلیت‌ها

- **انتقال انواع پیام**: متن، عکس، ویدئو، ویس، موسیقی، فایل (Document)، گیف (Animation)، لوکیشن و مخاطب.
- **سیستم تیکتینگ و پشتیبانی پیشرفته (مشابه Senfi)**: امکان ارسال تیکت با انتخاب موضوع دسته‌بندی، پیگیری تیکت‌ها و وضعیت آن‌ها توسط کاربر (`تیکت‌های من`)، مشاهده، فیلتر و پاسخ‌دهی کامل توسط ادمین در پنل مدیریت بدون نیاز به گروه پشتیبانی.
- **سیستم نظرسنجی پیشرفته (Polls)**: ایجاد نظرسنجی با گزینه‌های دلخواه توسط ادمین، ثبت رأی یکتای کاربران و نمایش درصد و نمودار بصری نتایج.
- **یکپارچگی با Redis**: ذخیره وضعیت (State) کاربران در Redis برای سرعت فوق‌العاده در پردازش پیام‌ها و حفظ ماندگاری وضعیت.
- **پشتیبانی از فایل‌های سنگین**: یکپارچه با ذخیره‌ساز ابری آروان (S3) و پاکسازی خودکار پس از آپلود.
- **سیستم مدیریت لیست سفید (Whitelist)**: امکان محدودسازی دسترسی ربات فقط به کاربران مجاز با کلید فعال‌سازی/غیرفعال‌سازی سریع.
- **پنل مدیریت کیبوردی (Reply Keyboard)**: رابط کاربری یکپارچه بدون نیاز به تایپ دستی با دکمه‌های Native تلگرام برای انتخاب مستقیم کاربر و گروه.
- **سیستم کش درون‌حافظه‌ای (In-Memory RAM Cache)**: پاسخ‌دهی بلادرنگ و به صفر رساندن بار کوئری‌های تکراری دیتابیس.
- **کنترل سقف کاربران**: قابلیت تعیین سقف کل کاربران ثبت‌نامی و سقف کاربران فعال.
- **عضویت اجباری (Join اجباری)**: بررسی عضویت کاربران در کانال‌های دلخواه با لینک شیشه‌ای و بررسی خودکار.
- **سامانه امنیتی کپچا سه‌گانه**: امکان فعال یا غیرفعال‌سازی تفکیک‌شده کد امنیتی ضداسپم برای تیکت‌ها، نظرسنجی‌ها و ارسال فایل‌ها توسط ادمین.
- **پشتیبان‌گیری آنلاین**: ارسال مستقیم فایل بک‌آپ دیتابیس در چت تلگرام برای ادمین.
- **داکریزه کامل**: دارای `Dockerfile` بهینه‌شده و `docker-compose.yml` آماده اجرا با Volume پایدار.

---

## 📋 پیش‌نیازها و توکن‌ها

1. **Telegram API ID & API Hash**: دریافت از [my.telegram.org](https://my.telegram.org)
2. **Telegram Bot Token**: دریافت از [@BotFather](https://t.me/BotFather)
3. **Bale Bot Token**: ساخت ربات در بله از طریق بازوی بات‌فادر بله و دریافت توکن
4. **Arvan Cloud S3 (اختیاری برای فایل‌های بزرگ)**: کلیدهای Access Key، Secret Key و Endpoint آروان

---

## 🚀 روش‌های نصب و راه‌اندازی

شما می‌توانید ربات را با **Docker** یا **بدون Docker (به‌صورت Native روی سرور لینوکس یا ویندوز)** نصب و اجرا کنید.

---

### روش ۱: راه‌اندازی با Docker و Docker Compose (پیشنهادی)

ساده‌ترین روش استقرار بدون درگیری با نصب پکیج‌های پایتون:

```bash
# ۱. دریافت سورس پروژه
git clone https://github.com/thehornet2002/tel2bale.git
cd tel2bale

# ۲. ساخت و تنظیم فایل .env
cp example.env .env
nano .env

# ۳. بیلد و اجرا در پس‌زمینه
docker compose up -d --build
```

**دستورات مدیریت کانتینر:**
```bash
docker compose logs -f       # مشاهده لاگ‌های زنده
docker compose restart       # ری‌استارت ربات
docker compose down          # توقف و بستن کانتینر
```

---

### روش ۲: نصب خودکار بدون داکر روی لینوکس (اسکریپت One-Line)

این اسکریپت به‌صورت خودکار پایتون، ابزارهای ساخت، کتابخانه‌ها، فایل `.env` و سرویس systemd را پیکربندی می‌کند:

```bash
bash <(curl -Ls https://raw.githubusercontent.com/thehornet2002/tel2bale/main/setup.sh)
```

اگر با کاربر غیر root وارد شده‌اید:
```bash
sudo -i
bash <(curl -Ls https://raw.githubusercontent.com/thehornet2002/tel2bale/main/setup.sh)
```

---

### روش ۳: نصب دستی بدون داکر روی لینوکس (Native + Systemd)

#### ۱. نصب وابستگی‌های سیستمی
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-dev build-essential libjpeg-dev zlib1g-dev git
```

#### ۲. دریافت پروژه و ساخت محیط مجازی
```bash
git clone https://github.com/thehornet2002/tel2bale.git
cd tel2bale

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

#### ۳. تنظیم فایل پیکربندی
```bash
cp example.env .env
nano .env
```

#### ۴. تست اجرای ربات
```bash
python main.py
```

#### ۵. اجرای دائمی در پس‌زمینه با سرویس Systemd
یک فایل سرویس در مسیر `/etc/systemd/system/tel2bale.service` بسازید:
```bash
sudo nano /etc/systemd/system/tel2bale.service
```

محتوای زیر را در آن قرار دهید (مسیر `/root/tel2bale` را با مسیر پوشه خود تطبیق دهید):
```ini
[Unit]
Description=Tel2Bale Bridge Bot Daemon
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/tel2bale
ExecStart=/root/tel2bale/.venv/bin/python /root/tel2bale/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

فعال‌سازی و شروع سرویس:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now tel2bale
```

دستورات مدیریت سرویس:
```bash
sudo systemctl status tel2bale     # بررسی وضعیت سرویس
sudo systemctl restart tel2bale    # ری‌استارت سرویس
sudo journalctl -u tel2bale -f     # مشاهده لاگ زنده
```

---

### روش ۴: اجرا در ویندوز (محیط تست و توسعه محلی)

در PowerShell:
```powershell
git clone https://github.com/thehornet2002/tel2bale.git
cd tel2bale

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt

copy example.env .env
notepad .env

python main.py
```

---

## ⚙️ متغیرهای محیطی (`.env`)

```env
# تنظیمات اصلی تلگرام
TEL_API_ID=1234567
TEL_API_HASH=abcdef0123456789abcdef0123456789
TEL_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TEL_ADMIN_IDS=123456789,987654321

# پیام‌های خوش‌آمدگویی و راهنما
TEL_START_TXT=به ربات انتقال پیام تلگرام به بله خوش آمدید.
TEL_HELP_TXT=ابتدا شناسه بله و توکن ربات بله خود را تنظیم کنید، سپس پیام‌ها را ارسال کنید.

# لیست سفید (Whitelist)
TEL_WHITELIST_ENABLED=False
TEL_WHITELIST_USERS=123456789,111222333

# محدودیت‌ها و کانال‌ها
TEL_ADS_CHANNELS=
TEL_MAX_FILE_SIZE=20
TEL_IN_MEMORY=False
DONATION_LINK=https://daramet.com/Hornet2002
SUPPORT_MESSAGE_LIMIT=5
MAX_USERS=0
MAX_ACTIVE_USERS=0

# تنظیمات ردیس (اختیاری جهت افزایش سرعت وضعیت کاربران)
REDIS_URL=redis://127.0.0.1:6379/0

# پروکسی تلگرام (اختیاری)
TEL_PROXY_SCHEME=
TEL_PROXY_HOST=
TEL_PROXY_PORT=

# پروکسی بله (اختیاری)
BALE_PROXY=
```

### جدول راهنمای متغیرها

| متغیر | مقدار پیش‌فرض | توضیحات |
|---|---|---|
| `TEL_API_ID` | اجباری | شناسه کاربری API تلگرام |
| `TEL_API_HASH` | اجباری | رشته هش API تلگرام |
| `TEL_BOT_TOKEN` | اجباری | توکن ربات تلگرام |
| `TEL_ADMIN_IDS` | اجباری | شناسه‌های عددی ادمین‌های اصلی (جدا شده با کاما) |
| `TEL_WHITELIST_ENABLED` | `False` | فعال‌سازی حالت لیست سفید در زمان استارت |
| `TEL_WHITELIST_USERS` | - | لیست اولیه شناسه‌های مجاز در لیست سفید |
| `TEL_MAX_FILE_SIZE` | `20` | حداکثر حجم فایل برای ارسال مستقیم (مگابایت) |
| `MAX_USERS` | `0` | سقف کل کاربران ثبت‌نامی (0 = نامحدود) |
| `MAX_ACTIVE_USERS` | `0` | سقف کاربران دارای توکن/شناسه بله فعال (0 = نامحدود) |
| `SUPPORT_MESSAGE_LIMIT` | `5` | سقف تیکت‌های در انتظار پاسخ هر کاربر |
| `REDIS_URL` | - | آدرس اتصال به ردیس (مثال: `redis://127.0.0.1:6379/0`) |
| `BALE_PROXY` | - | آدرس پروکسی برای دسترسی سرور به API بله |

---

## 📂 ساختار فایل‌های پروژه

```text
tel2bale/
├── Dockerfile                   # ایمیج بهینه‌شده مبتنی بر python:3.12-slim
├── docker-compose.yml           # کانفیگ چندکانتینری داکر همراه با Volumeها
├── main.py                      # نقطه شروع اجرای بات، ثبت کامندها و کلاینت
├── config.py                    # مدیریت متغیرهای محیطی با قفل Async و اعتبارسنجی
├── requirements.txt             # نیازمندی‌های پایتون
├── example.env                  # نمونه متغیرهای کانفیگ
│
├── db/
│   ├── db_async.py              # مدیریت نشست‌ها و اتصالات غیرمسدودکننده SQLite
│   ├── model_async.py           # مدل‌های داده، کش رم و کوئری‌های Async
│   └── backup.py                # ماژول تولید فایل پشتیبان امن از دیتابیس
│
├── handlers/
│   ├── commands.py              # هندلرهای کامندهای /start ، /help و /panel
│   ├── callback.py              # هندلرهای دکمه‌های Inline
│   ├── messages.py              # مدیریت پیام‌های متنی، حالت‌های ادمین و فوروارد
│   └── handler_helpers/
│       ├── command_helper.py
│       ├── callback_helpers/
│       │   ├── navigation_handler.py
│       │   ├── user_handler.py
│       │   └── admin/       # کنترلرهای بخش‌های مختلف پنل ادمین
│       └── message_helpers/
│           ├── admin_handler.py
│           ├── forward_handler.py
│           ├── common.py
│           └── ...
│
├── services/
│   ├── bale_service.py          # ارتباط با API بله با مکانیسم Retry و هندل هوشمند بایت‌ها
│   ├── s3_service.py            # ارتباط با باکت S3 آروان و تولید لینک موقت
│   └── quota_service.py         # مدیریت همزمانی سهمیه دانلود
│
├── utils/
│   ├── filters.py               # فیلترهای سفارشی تلگرام (جوئین اجباری، ظرفیت، لیست سفید)
│   ├── keyboards.py             # کیبوردهای شیشه‌ای و کیبوردهای Reply ادمین
│   ├── logger.py                # لاگر چرخشی
│   └── parser.py                # اعتبارسنجی لینک‌ها و آدرس‌های ورودی
│
└── tests/
    └── test_self_check.py       # تست‌های داخلی و اعتبارسنجی جامع پروژه
```

---

## 🛠️ قابلیت‌های پنل مدیریت

ادمین‌های ربات می‌توانند با ارسال دستور `/admin` یا `/panel` به پنل مدیریت با کلیدهای راحت دسترسی پیدا کنند:

- 💾 **دریافت دیتابیس**: ارسال مستقیم فایل دیتابیس در چت تلگرام.
- 🎫 **تیکت‌های پشتیبانی**: مدیریت و مشاهده لیست تیکت‌ها و ارسال پاسخ مستقیم به کاربران بدون نیاز به گروه.
- 🗂 **موضوعات تیکت**: افزودن موضوع جدید (عادی یا ناشناس) و حذف/آرشیو دسته‌بندی‌ها.
- 📊 **مدیریت نظرسنجی‌ها**: ایجاد نظرسنجی‌های جدید با گزینه‌های متعدد، فعال/بستن و مشاهده زنده نتایج.
- 🔐 **تنظیمات کپچا**: امکان فعال یا غیرفعال‌سازی هوشمند کد امنیتی برای تیکت‌ها، نظرسنجی‌ها و ارسال فایل.
- 🛡️ **مدیریت لیست سفید (Whitelist)**: افزودن، حذف، مشاهده اعضا و تغییر وضعیت فعال/غیرفعال بودن ربات.
- 🚫 **مسدودسازی (بن/آنبن)**: قابلیت مسدود کردن با آیدی عددی تلگرام یا آیدی بله (با دکمه مستقیم انتخاب کاربر).
- ➕/➖ **مدیریت ادمین‌ها**: ارتقای کاربر به ادمین یا سلب دسترسی با ذخیره‌سازی دائمی.
- 🌐/👤 **تنظیم محدودیت حجم**: اعمال سقف دانلود روی تمام کاربران یا یک کاربر مشخص (گیگابایت).
- 👥/🟢 **سقف کاربران کل و فعال**: کنترل دقیق ظرفیت ورودی به ربات.
- 📢/✉️ **ارسال پیام**: ارسال پیام همگانی (Broadcast) یا ارسال پیام اختصاصی به یک کاربر.
- 🔗/❌ **مدیریت عضویت اجباری**: تنظیم و حذف کانال‌های عضویت اجباری تلگرام.
- ☕ **تغییر لینک حمایت مالی**: تغییر آدرس لینک دونیت به صورت زنده.

---

## 🧪 تست و اعتبارسنجی

پروژه دارای سوئیت تست خودکار داخلی است که بخش‌های حساس، اعتبارسنجی URLها، قوانین دیتابیس، سیستم Whitelist و فیلترها را بررسی می‌کند:

```bash
# اجرای خودکار تست‌ها در محیط مجازی
python tests/test_self_check.py
```

---

## 🤝 مشارکت

از پیشنهادات و Pull Requestها استقبال می‌شود:
1. مخزن را Fork کنید.
2. برنچ جدید بسازید (`git checkout -b feature/awesome-feature`).
3. تغییرات خود را Commit کنید (`git commit -m "feat: add awesome feature"`).
4. برنچ را Push کنید و یک PR ثبت کنید.

---

## 📜 لایسنس

این پروژه تحت لایسنس **[MIT](LICENSE)** منتشر شده است.
