#  موسیقی شیراز — Django Music School Management System

A modular, production-ready Django (MVT) music school management system for an
academy in Shiraz, Iran. Fully Persian / RTL, with Zarinpal payment integration.

> **Stack:** Django 5 · Django Templates + Tailwind (CDN) + Vanilla JS ·
> SQLite (swap for Postgres in prod) · Zarinpal Request/Verify API ·
> Persian (fa) / RTL / Asia/Tehran.

---

## ⚠️ About this environment

This code is delivered as **pure Django source code**. The sandbox it was
generated in only runs a Next.js dev server, so the Django project **cannot be
executed or previewed inside that sandbox**. Run it on your own machine /
server with the commands below.

---

## Project structure

```
django_music_school/
├── manage.py
├── requirements.txt
├── .env.example              # copy to .env
├── config/                   # project settings, urls, wsgi/asgi
│   ├── settings.py
│   └── urls.py
├── apps/
│   ├── accounts/             # custom User (phone login, roles, profile)
│   ├── school/               # Teacher, Course, Class, Enrollment
│   ├── tickets/              # Ticket, TicketMessage        (Step 3)
│   ├── payments/             # Payment model + Zarinpal helper/views
│   └── core/                 # public website (landing, courses, invoice)
├── templates/
│   ├── base.html             # RTL, Vazirmatn, Tailwind CDN, sticky footer
│   ├── core/                 # landing, course_list, course_detail, invoice
│   └── payments/             # verify_success / verify_fail
├── static/
└── media/                    # uploaded avatars
```

---

## Setup

```bash
# 1. Create & activate a virtualenv
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
#   edit .env  -> set SECRET_KEY, ZARINPAL_MERCHANT_ID, ZARINPAL_SANDBOX, SITE_URL

# 4. Apply migrations
python manage.py migrate

# 5. (optional) load sample data — admin + 4 teachers + 6 courses + 6 classes
python manage.py seed_data
#   admin login: 09120000000 / admin12345

# 6. Run the dev server
python manage.py runserver
```

Open <http://localhost:8000>.

---

## What's included so far

| Area | Step 1 | Step 2 |
|------|:------:|:------:|
| Models: User, Teacher, Course, Class, Enrollment, Ticket, TicketMessage, Payment | ✅ | |
| Landing page (hero, intro, courses, CTA) | ✅ | |
| Courses list page | ✅ | |
| Course detail page (instructor, price, description, schedule) | ✅ | |
| Invoice / checkout page (name, phone, national ID → Zarinpal) | ✅ | |
| Zarinpal `request_payment` + redirect to gateway | ✅ | |
| Django admin for every model | ✅ | |
| Seed command (`seed_data`) | ✅ | |
| **Student login & register** (phone-based, role-aware) | | ✅ |
| **Separate admin login page** | | ✅ |
| **Role-based decorators** (`student_required`, `admin_required`) | | ✅ |
| **Full Zarinpal verify** (verify → SUCCESS + ref_id → auto Enrollment → auto-login) | | ✅ |
| **Idempotent re-verify** (no duplicate enrolment on refresh) | | ✅ |
| **Authenticated invoice** (reuses logged-in user, prefills form) | | ✅ |
| **Dynamic nav** (login/register vs name/dashboard/logout) | | ✅ |
| **Student dashboard stub** (enrollments + recent payments) | | ✅ |
| **Admin dashboard stub** (basic stats) | | ✅ |
| Student dashboard — full panel (weekly classes, events) | ⏭ | ✅ Step 3 |
| Tickets (AJAX create/list + detail/reply) | ⏭ | ✅ Step 3 |
| Profile page (edit + avatar upload) | ⏭ | ✅ Step 3 |
| Persian (Jalali) date filter + Persian number formatting | ⏭ | ✅ Step 3 |
| Admin dashboard — full (classes management, directory, search/filters) | ⏭ | ✅ Step 4 |

---

## Zarinpal

- Set `ZARINPAL_SANDBOX=True` while developing (uses Zarinpal sandbox endpoints).
- Put your real merchant UUID in `ZARINPAL_MERCHANT_ID`.
- `SITE_URL` must be the public URL Zarinpal can redirect back to.

The flow lives in `apps/payments/zarinpal.py` and `apps/payments/views.py`:

1. Invoice form POST → creates a `Payment(PENDING)` → redirects to
   `/payments/request/<id>/`.
2. `zarinpal_request` calls the gateway, stores `authority`, redirects the
   browser to the Zarinpal hosted page.
3. Zarinpal redirects back to `/payments/verify/?Status=OK&Authority=...`.
4. `zarinpal_verify` (full DB update in Step 2) verifies & shows the result.

---

## Producing a production Tailwind build (optional)

Templates ship with the Tailwind CDN for zero-config styling. For production,
replace the CDN `<script>` in `templates/base.html` with a compiled
`static/css/tailwind.css` built via the Tailwind CLI.
