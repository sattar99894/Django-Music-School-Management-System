# 🎵 موسیقی شیراز — سیستم مدیریت آموزشگاه موسیقی با Django

یک سیستم مدیریت آموزشگاه موسیقی کامل، ماژولار و آماده‌ی تولید با Django 5 و Poetry.
این پروژه برای یک آموزشگاه موسیقی در شیراز طراحی شده و از درگاه زرین‌پال، احراز هویت مبتنی بر شماره تلفن، داشبورد دانشجو و ادمین، سیستم تیکتینگ و پنل مدیریتی اختصاصی پشتیبانی می‌کند.

✅ **کاملاً راست‌چین (RTL)** · **پشتیبانی از تاریخ شمسی** · **اعداد فارسی** · **قالب‌های Tailwind CSS**

---

## 📦 پیش‌نیازها
* **Python 3.10** یا بالاتر
* **Poetry** برای مدیریت وابستگی‌ها
* *(اختیاری)* PostgreSQL برای محیط تولید

---

## 🚀 نصب و راه‌اندازی سریع
```bash
# ۱. دریافت کد پروژه
git clone https://github.com/your-username/django-music-school.git
cd django-music-school

# ۲. نصب وابستگی‌ها با Poetry
poetry install

# ۳. کپی فایل محیط و تنظیم متغیرها
cp .env.example .env
# سپس .env را ویرایش کرده و SECRET_KEY، ZARINPAL_MERCHANT_ID و ... را تنظیم کنید.

# ۴. اجرای مایگریشن‌ها
poetry run python manage.py migrate

# ۵. (اختیاری) بارگذاری داده‌های نمونه
poetry run python manage.py seed_data
# کاربر ادمین: 09120000000 / رمز: admin12345

# ۶. اجرای سرور توسعه
poetry run python manage.py runserver
بازدید کنید: `http://localhost:8000`

---

## 🌳 ساختار درختی پروژه

text
django_music_school/
├── manage.py
├── pyproject.toml
├── poetry.lock
├── .env
├── .gitignore
├── README.md
│
├── config/                         # تنظیمات اصلی پروژه
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── apps/                           # تمام اپلیکیشن‌های پروژه
│   ├── __init__.py
│   │
│   ├── accounts/                   # مدیریت کاربران، احراز هویت، نقش‌ها
│   │   ├── migrations/
│   │   ├── admin.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── forms.py
│   │   └── ...
│   │
│   ├── school/                     # مدل‌های آموزشگاه (Teacher, Course, Class, Enrollment)
│   ├── tickets/                    # سیستم تیکتینگ
│   ├── payments/                   # پرداخت‌ها و درگاه زرین‌پال
│   ├── core/                       # صفحات عمومی سایت و تگ‌های قالب (persian_tags)
│   └── admin_panel/                # پنل مدیریت اختصاصی ادمین
│
├── templates/                      # قالب‌های HTML
│   ├── base.html                   # قالب پایه (RTL، Tailwind)
│   ├── core/
│   ├── accounts/
│   ├── admin_panel/
│   └── payments/
│
├── static/                         # فایل‌های ایستا
│   └── js/
│
└── media/                          # فایل‌های آپلودی (آواتارها)
└── avatars/

---

## ✨ ویژگی‌های اصلی

### 👥 احراز هویت و نقش‌ها
* ورود / ثبت‌نام با شماره تلفن (بدون نام کاربری)
* دو نقش دانشجو و ادمین با دکوریتورهای دسترسی مجزا
* صفحه ورود اختصاصی برای ادمین‌ها

### 🎓 بخش آموزشگاه
* مدل‌های استاد، دوره، کلاس و ثبت‌نام
* نمایش لیست دوره‌ها و جزئیات هر دوره
* امکان ثبت‌نام در دوره از طریق فاکتور و پرداخت آنلاین

### 💳 پرداخت با زرین‌پال
* درخواست پرداخت با ایجاد Payment و دریافت Authority
* بازگشت به سایت و تأیید خودکار پرداخت
* ثبت‌نام خودکار دانشجو در دوره پس از تأیید پرداخت (idempotent)
* نمایش شماره مرجع و وضعیت تراکنش

### 🎫 سیستم تیکتینگ (پشتیبانی)
* دانشجویان می‌توانند تیکت ایجاد کنند و پیام بفرستند
* پاسخ ادمین و مشاهدهٔ گفتگو (با AJAX)
* لیست تیکت‌ها با وضعیت (باز/بسته)

### 📊 داشبوردها
* **داشبورد دانشجو:** نمایش کلاس‌های هفته، رویدادها، تیکت‌ها و پرداخت‌های اخیر
* **داشبورد ادمین:** آمار کلی، مدیریت کلاس‌ها، جستجو و فیلتر دانشجویان و کلاس‌ها

### 🧰 ابزارهای جانبی
* فیلترهای قالب برای تاریخ شمسی و اعداد فارسی
* آپلود آواتار برای کاربران
* اسکریپت `seed_data` برای تولید داده‌های نمونه

---

## 🧪 دستورات مفید Poetry

| کاربرد | دستور |
| :--- | :--- |
| **نصب وابستگی‌ها** | `poetry install` |
| **اضافه کردن پکیج** | `poetry add <package>` |
| **حذف پکیج** | `poetry remove <package>` |
| **اجرای سرور توسعه** | `poetry run python manage.py runserver` |
| **ساخت مایگریشن** | `poetry run python manage.py makemigrations` |
| **اعمال مایگریشن** | `poetry run python manage.py migrate` |
| **وارد شدن به shell جنگو** | `poetry run python manage.py shell` |
| **اجرای تست‌ها** | `poetry run python manage.py test` |
| **اجرای اسکریپت seed** | `poetry run python manage.py seed_data` |

---

## ⚙️ متغیرهای محیطی (فایل `.env`)

env
SECRET_KEY=your-secret-key-here
DEBUG=True
SITE_URL=http://localhost:8000

ZARINPAL_MERCHANT_ID=your-merchant-id
ZARINPAL_SANDBOX=True

# دیتابیس (اختیاری)
DB_NAME=db.sqlite3
# برای PostgreSQL:
# DB_ENGINE=django.db.backends.postgresql
# DB_NAME=mydb
# DB_USER=myuser
# DB_PASSWORD=mypass
# DB_HOST=localhost
# DB_PORT=5432
> ⚠️ در محیط تولید حتماً `DEBUG=False` و `ZARINPAL_SANDBOX=False` تنظیم شود.

---

## 🗂️ دیتابیس و مدل‌ها
پروژه از SQLite به‌عنوان پیش‌فرض استفاده می‌کند (قابل تعویض با PostgreSQL). مدل‌های اصلی عبارتند از:
* **User:** پیش‌فرض سفارشی با `phone` به‌عنوان شناسه
* **Teacher:** استادان
* **Course:** دوره‌های آموزشی
* **Class:** کلاس‌های هر دوره با زمان و مکان
* **Enrollment:** ثبت‌نام دانشجو در کلاس
* **Ticket و TicketMessage:** تیکت‌های پشتیبانی
* **Payment:** تراکنش‌های زرین‌پال

---

## 🛠️ تکنولوژی‌های استفاده‌شده
* **Backend:** Django 5
* **Frontend:** Tailwind CSS (CDN) + Vanilla JS
* **Payment:** Zarinpal REST API
* **Package Manager:** Poetry
* **Database:** SQLite (توسعه) / PostgreSQL (تولید)
* **Localization:** Persian (fa-IR), RTL, Asia/Tehran timezone

---

## 📝 نکات توسعه
* تمام اپلیکیشن‌ها در پوشهٔ `apps/` قرار دارند و با پیشوند `apps.` در `INSTALLED_APPS` معرفی شده‌اند.
* قالب‌ها از `base.html` ارث‌بری می‌کنند که شامل فایل‌های استایل پایه، فوتر چسبنده و اسکریپت‌های مشترک است.
* برای فیلترهای فارسی، از `templatetags/persian_tags.py` استفاده کنید (بارگذاری با `{% load persian_tags %}`).
* مسیرهای اپلیکیشن‌ها در `config/urls.py` مدیریت می‌شوند.

---

## 🚢 استقرار در تولید
۱. متغیرهای محیطی را برای تولید تنظیم کنید (`DEBUG=False`, `ZARINPAL_SANDBOX=False`).
۲. دیتابیس را به PostgreSQL یا هر DB تولیدی تغییر دهید.
۳. فایل‌های استاتیک را جمع‌آوری کنید:
bash
poetry run python manage.py collectstatic
۴. از یک وب‌سرور مانند Gunicorn یا uWSGI استفاده کنید.
۵. برای Tailwind، اسکریپت CDN را با یک فایل کامپایل‌شده جایگزین کنید (با استفاده از Tailwind CLI).
