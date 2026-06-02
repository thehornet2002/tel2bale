# 🚀 ربات هوشمند انتقال پیام تلگرام به بله
## TEL2BALE : Telegram to Bale Bridge Bot
<div align="center">

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen)](https://github.com/thehornet2002/tel2bale)

</div>


## 📌 درباره پروژه

**این پروژه در زمان قطعی اینترنت یا کندی آن در ایران کاربردی است، با این ربات شما می توانید تا حجمی که بله از آن پشتیبانی می کند از  تلگرام پیام ها را همراه با media آن به بله منتقل کنید.**



## 📋 پیش‌نیازها

قبل از شروع، موارد زیر را آماده کنید:

### 🖥️ سخت‌افزار و سامانه‌عامل
- **سرور Linux:** Debian 11+ یا Ubuntu 20.04+
- **حافظه:** حداقل 512 MB RAM
- **دیسک:** حداقل 1 GB فضای خالی
- **پردازنده:** هر پردازنده‌ای کافی است

### 🔧 نرم‌افزار
- **Python:** 3.10 یا بالاتر
- **pip:** مدیریت بسته‌های Python
- **git:** (اختیاری برای دانلود)

### 🔑 API Keys و توکن‌ها

#### 📱 توکن تلگرام
1. به [@BotFather](https://t.me/botfather) در تلگرام بروید
2. دستور `/newbot` را ارسال کنید
3. نام و نام‌کاربری ربات را وارد کنید
4. **Bot Token** را کپی کنید

#### 🔐 API ID و API Hash تلگرام
1. به [my.telegram.org](https://my.telegram.org) بروید
2. با شماره‌ی خود وارد شوید
3. روی **API development tools** کلیک کنید
4. **API ID** و **API Hash** را کپی کنید

#### 🟢 توکن بله
1. به [@BaleBot](https://ble.ir/botfather) در بله بروید
2. دستور `/newbot` را ارسال کنید
3. **Bot Token** بله را کپی کنید

---

## 🚀 راهنمای راه‌اندازی

### روش 1️⃣: نصب خودکار (توصیه شده)

```bash
# دریافت و اجرای اسکریپت خودکار
sudo bash <(curl -Ls https://raw.githubusercontent.com/thehornet2002/tel2bale/main/setup.sh)
```

**اسکریپت خودکار این کارها را انجام می‌دهد:**
1. نصب تمام وابستگی‌های سیستم
2. نصب Python 3.10+
3. ایجاد Virtual Environment
4. نصب تمام کتابخانه‌های Python
5. ایجاد فایل `.env`
6. راه‌اندازی سرویس systemd

### روش 2️⃣: نصب دستی

```bash
# 1️⃣ نصب وابستگی‌های سیستم
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev build-essential

# 2️⃣ دانلود پروژه
git clone https://github.com/thehornet2002/tel2bale.git
cd Tel2Bale

# 3️⃣ ایجاد Virtual Environment
python3.12 -m venv venv
source venv/bin/activate

# 4️⃣ نصب وابستگی‌های Python
pip install --upgrade pip
pip install -r requirements.txt

# 5️⃣ ایجاد فایل .env
cp example.env .env
nano .env  # ویرایش توکن‌ها

# 6️⃣ اجرای ربات
python main.py
```

---

## ⚙️ پیکربندی (.env)

فایل `.env` را ایجاد کرده و متغیرهای زیر را تنظیم کنید:

```env
# 📱 API تلگرام
TEL_API_ID=123456789              # API ID از my.telegram.org
TEL_API_HASH=abcdef123456         # API Hash از my.telegram.org
TEL_BOT_TOKEN=123:ABC-XYZ         # Token از @BotFather

# 🔑 شناسه مدیریت‌کنندگان
TEL_ADMIN_IDS=123456789,987654321 # شناسه‌های عددی ادمین‌ها (جدا شده با کاما)

# 📊 تنظیمات فایل
TEL_MAX_FILE_SIZE=20              # حداکثر اندازه فایل به MB
TEL_IN_MEMORY=False               # نگهداری فایل در RAM (True/False)

# 📢 تنظیمات پیام‌های ویژه
TEL_START_TXT="خوش آمدید!"        # متن پیام /start
TEL_HELP_TXT="راهنما..."          # متن پیام /help

# 📡 کانال‌های تبلیغاتی
TEL_ADS_CHANNELS=channel1,channel2                 # شناسه کانال‌های تبلیغاتی، ID کانال بدون @  (اختیاری)

# 🌐 تنظیمات Proxy (اختیاری)
TEL_PROXY_SCHEME=                 # نوع Proxy (http/https/socks5)
TEL_PROXY_HOST=                   # آدرس Proxy
TEL_PROXY_PORT=                   # درگاه Proxy
```

---

## 📂 ساختار پروژه

```
Tel2Bale/
├── 📄 main.py                    # نقطه ورود اصلی برنامه
├── 📄 config.py                  # خواندن متغیرهای محیطی
├── 📄 requirements.txt            # کتابخانه‌های Python
├── 📄 .env                        # متغیرهای محیطی
├── 📄 example.env                 # نمونه فایل .env
│
├── 📁 handlers/                   # مدیریت پیام‌ها و دستورات
│   ├── commands.py               # دستورات (/start, /help)
│   ├── messages.py               # پیام‌های عادی کاربران
│   ├── callbacks.py              # کلیک دکمه‌های شیشه‌ای
│   └── handler_helpers/
│       ├── command_helper.py     # توابع کمکی دستورات
│       ├── messages_helper.py    # منطق اصلی انتقال پیام
│       └── callback_helper.py    # منطق کلیک دکمه‌ها
│
├── 📁 services/                  # سرویس‌های خارجی
│   ├── bale_service.py           # ارسال پیام به بله
│   └── quota_service.py          # مدیریت سهمیه مصرف
│
├── 📁 db/                        # دیتابیس
│   ├── db_sync.py                # اتصال Sync به DB
│   ├── db_async.py               # اتصال Async به DB
│   ├── model_sync.py             # مدل‌های Sync
│   └── model_async.py            # مدل‌های Async
│
└── 📁 logs/                      # فایل‌های لاگ
    └── bot.log                   # لاگ‌های ربات
```

---

## 🔄 نمودار جریان داده

```
┌─────────────────────────────────────────────────────────────┐
│  کاربر ارسال پیام در تلگرام                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  handlers/messages.py  │
        │  دریافت پیام          │
        └────────────┬───────────┘
                     │
                     ▼
        ┌────────────────────────────────┐
        │ بررسی وضعیت کاربر             │
        │ (State Check)                  │
        └────────────┬───────────────────┘
                     │
           ┌─────────┴─────────┐
           │                   │
          ممنوع              مجاز
           │                   │
           ▼                   ▼
     ┌──────────┐        ┌──────────┐
     │ Forward  │        │ Message  │
     │ Logic   │        │ Denied   │
     └────┬─────┘        └──────────┘
          │
          ▼
    ┌─────────────────┐
    │ Check File Size │
    │ (بررسی حجم)      │
    └────┬────────────┘
         │
    ┌────┴──────┐
    │            │
   < 20MB      > 20MB
    │            │
    ▼            ▼
 Download        Drop 
 & Send 
 To Bale
     │
     ▼
┌──────────────────────┐
│ bale_service.py      │
│ ارسال به بله         │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ quota_service.py     │
│ کاهش سهمیه مصرف      │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ db/model_async.py    │
│ ذخیره در دیتابیس     │
└──────────────────────┘
```

---

## 📚 معرفی ماژول‌های اصلی

### 🎛️ Handlers
**وظیفه:** مدیریت پیام‌های تلگرام

| فایل | توضیح |
|------|-------|
| `commands.py` | پردازش دستورات (`/start`, `/help`, `/admin`) |
| `messages.py` | شنود پیام‌های متنی و رسانه‌ای |
| `callbacks.py` | مدیریت کلیک دکمه‌های شیشه‌ای |

### 🔧 Services
**وظیفه:** برقراری ارتباط با سرویس‌های خارجی

| فایل | توضیح |
|------|-------|
| `bale_service.py` | ارسال پیام/عکس/ویدیو/صوت/مستند به بله |
| `quota_service.py` | بررسی و مدیریت سهمیه مصرف کاربران |

### 💾 Database
**وظیفه:** ذخیره‌سازی اطلاعات

| فایل | توضیح |
|------|-------|
| `db_async.py` | اتصال ناهمگام به دیتابیس |
| `model_async.py` | تعریف جداول و کوئری‌های دیتابیسی |

**جداول اصلی:**
- `users` - اطلاعات کاربران
- `supports` - پیام‌های پشتیبانی
- `settings` - تنظیمات پروژه

---

## 🎮 نحوه استفاده

### برای کاربران عادی

```
/start          - شروع ربات و دریافت منو
/help           - مشاهده راهنمای استفاده
```

سپس:
1. شناسه بله خود را وارد کنید
2. توکن بله را وارد کنید
3. فایل‌های خود را برای انتقال ارسال کنید

### برای مدیریت‌کنندگان

```
منوی مدیریت:
├── دریافت دیتابیس
├── بن و آنبن ID بله
├── بن و آنبن ID تلگرام
├── نمایش 10 کاربر پر مصرف
├── مشاهده پیام های پشتیبانی
├── تنظیم محدودیت برای افراد
├── حذف و اضافه کردن Join اجباری
├── ارسال پیام به استفاده کنندگان ربات
└── کم و اضافه کردن ادمین
```

---

## 🐛 رفع مشکل (Troubleshooting)

### ❌ خطای "Python.h: No such file or directory"

**دلیل:** کتابخانه‌های توسعه Python نصب نشده‌اند

**حل:**
```bash
sudo apt install python3.12-dev build-essential
```

### ❌ خطای "venv: No module named venv"

**دلیل:** بسته venv نصب نشده است

**حل:**
```bash
sudo apt install python3.12-venv
```

### ❌ ربات راه‌اندازی نمی‌شود

**وضعیت ربات را بررسی کنید:**
```bash
sudo systemctl status Tel2Bale
```

**مشاهده لاگ‌ها:**
```bash
sudo journalctl -u Tel2Bale -f -n 50
```

**راه‌اندازی مجدد:**
```bash
sudo systemctl restart Tel2Bale
```

### ❌ خطای "Connection refused"

**دلیل:** دیتابیس اتصال ندارد

**حل:**
```bash
# بررسی وضعیت دیتابیس
sudo systemctl status postgresql

# شروع دیتابیس
sudo systemctl start postgresql
```

### ❌ فایل‌ها به بله ارسال نمی‌شوند

**بررسی نکات:**
1. ✓ توکن بله صحیح است؟
2. ✓ شناسه بله صحیح است؟
3. ✓ حجم فایل از 20 MB کمتر است؟
4. ✓ اتصال اینترنت برقرار است؟

**لاگ را بررسی کنید:**
```bash
sudo journalctl -u Tel2Bale -f | grep -i error
```

---

## 📊 دستورات مفید

### مدیریت سرویس

```bash
# وضعیت ربات
sudo systemctl status Tel2Bale

# شروع ربات
sudo systemctl start Tel2Bale

# متوقف کردن ربات
sudo systemctl stop Tel2Bale

# راه‌اندازی مجدد
sudo systemctl restart Tel2Bale

# فعال‌سازی شروع خودکار
sudo systemctl enable Tel2Bale
```

### مشاهده لاگ‌ها

```bash
# 50 خط آخر لاگ
sudo journalctl -u Tel2Bale -n 50

# پیام‌های خطا
sudo journalctl -u Tel2Bale | grep -i error

# لاگ زنده (Real-time)
sudo journalctl -u Tel2Bale -f

# لاگ‌های آخر 24 ساعت
sudo journalctl -u Tel2Bale --since "24 hours ago"
```

### مدیریت دیتابیس

```bash
# بررسی کاربران
psql -U telegram -d tel2bale -c "SELECT * FROM users LIMIT 10;"

# حذف کاربر
psql -U telegram -d tel2bale -c "DELETE FROM users WHERE id=123;"

# مشاهده آمار
psql -U telegram -d tel2bale -c "SELECT COUNT(*) FROM users;"
```

---

## 🔐 نکات امنیتی

### ⚠️ مهم

1. **فایل .env را محفوظ نگه‌دارید**
   - از اشتراک‌گذاری کلید‌های API خودداری کنید

3. **توکن‌ها را به‌طور منظم تغییر دهید**
   - هر 3 ماه یک بار توکن جدید ایجاد کنید

4. **لاگ‌های حساس را حذف کنید**
   ```bash
   sudo journalctl --vacuum-time=30d
   ```

---

## 📈 بهبود و توسعه

### برنامه‌های آینده

- [ ] اضافه کردن لینک دونیت در .env
- [ ] اضافه کردن S3 Endpoint برای استفاده از دیگر سرویس های ذخیره سازی ابری
- [ ] اضافه کردن تغییر لینک دونیت در پنل مدیریت
- [ ] اضاقه کردن محدودیت در تعداد user و تعداد user فعال
- [ ] حذف message_support از دیتابیس و اضافه کردن گروه پشتیبانی و محدودیت ارسال پیام به پشتیبانی

---

## 🤝 مشارکت

اگر مایل به مشارکت هستید:

1. **Fork** کنید
2. **Branch** جدید ایجاد کنید (`git checkout -b feature/amazing-feature`)
3. **تغییرات** را commit کنید (`git commit -m 'Add amazing feature'`)
4. **Push** کنید (`git push origin feature/amazing-feature`)
5. **Pull Request** ایجاد کنید

---

## 📞 پشتیبانی و ارتباط

### 🆘 کمک و پشتیبانی

- **Issues:** [بازکردن Issue](https://github.com/thehornet2002/tel2bale/issues)
- **Discussions:** [پرسش و پاسخ](https://github.com/thehornet2002/tel2bale/discussions)
- **تلگرام:** [@tel2bale](https://t.me/tel2bale)

### 👤 نویسنده

**TheHornet2002**
- GitHub: [@thehornet2002](https://github.com/thehornet2002)
- Telegram: [@thehornet2002](https://t.me/thehornet2002)

---

## 📜 لایسنس

این پروژه تحت لایسنس **MIT** است. برای اطلاعات بیشتر [LICENSE](LICENSE) را ببینید.

---

## ⭐ حمایت

اگر این پروژه برایتان مفید بود، ⭐ **Star** دهید!

---

<div align="center">

**ساخته شده با ❤️ برای جامعه تلگرام**

[⬆ بالا رفتن](#-ربات-هوشمند-انتقال-پیام-تلگرام-به-بله)

</div>
