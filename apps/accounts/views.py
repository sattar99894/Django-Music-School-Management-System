"""
Accounts views — authentication + full student panel.

Step 3 adds:
    * Dashboard home (weekly schedule + today's classes + stats + events)
    * Tickets list + AJAX create
    * Ticket detail + AJAX reply
    * Profile (edit + avatar upload)
"""
import json

import jdatetime
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from apps.accounts.models import User
from apps.payments.models import Payment
from apps.school.models import Class, Enrollment
from apps.tickets.models import Ticket, TicketMessage

from .forms import ProfileForm, RegisterForm
from .utils import build_weekly_schedule, today_persian_day


# ==================================================================
# Authentication
# ==================================================================
def login_view(request):
    if request.user.is_authenticated and request.user.role != User.Role.ADMIN:
        return redirect("auth:dashboard")

    error = None
    if request.method == "POST":
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, phone=phone, password=password)

        if user is None:
            error = "شماره موبایل یا رمز عبور اشتباه است."
        elif user.role == User.Role.ADMIN:
            error = "مدیران باید از صفحه ورود مدیران استفاده کنند."
        else:
            login(request, user)
            nxt = request.GET.get("next") or reverse("auth:dashboard")
            return redirect(nxt)

    return render(request, "accounts/login.html", {"error": error})


def register_view(request):
    if request.user.is_authenticated and request.user.role != User.Role.ADMIN:
        return redirect("auth:dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("auth:dashboard")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("core:landing")


def admin_login_view(request):
    if request.user.is_authenticated and request.user.role == User.Role.ADMIN:
        return redirect("admin_panel:dashboard")

    error = None
    if request.method == "POST":
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, phone=phone, password=password)

        if user is None:
            error = "اطلاعات واردشده اشتباه است."
        elif user.role != User.Role.ADMIN:
            error = "این حساب کاربری دسترسی مدیر ندارد."
        else:
            login(request, user)
            return redirect("admin_panel:dashboard")

    return render(request, "accounts/admin_login.html", {"error": error})


# ==================================================================
# Student dashboard
# ==================================================================
@login_required(login_url="auth:login")
def dashboard(request):
    """Dashboard home: weekly class schedule + today's classes + stats."""
    if request.user.role == User.Role.ADMIN:
        return redirect("admin_panel:dashboard")

    enrollments = (
        request.user.enrollments.select_related(
            "class_ref__course", "class_ref__teacher__user"
        ).order_by("-created_at")
    )
    active_enrollments = [e for e in enrollments if e.status == Enrollment.Status.ENROLLED]

    weekly = build_weekly_schedule(enrollments)
    today_day = today_persian_day()
    today_classes = weekly.get(today_day, [])

    # Upcoming classes = today + following days (ordered), flattened.
    upcoming = []
    from .utils import PERSIAN_DAYS, persian_weekday_index
    idx = persian_weekday_index()
    ordered_days = PERSIAN_DAYS[idx:] + PERSIAN_DAYS[:idx]
    for d in ordered_days:
        for item in weekly.get(d, []):
            upcoming.append({**item, "day": d})
    upcoming = upcoming[:5]

    stats = {
        "active_courses": len(active_enrollments),
        "today_classes": len(today_classes),
        "open_tickets": request.user.tickets.filter(
            status__in=[Ticket.Status.OPEN, Ticket.Status.ANSWERED]
        ).count(),
        "success_payments": request.user.payments.filter(
            status=Payment.Status.SUCCESS
        ).count(),
    }
    recent_payments = request.user.payments.order_by("-created_at")[:5]

    return render(
        request,
        "accounts/dashboard.html",
        {
            "weekly": weekly,
            "today_day": today_day,
            "today_classes": today_classes,
            "upcoming": upcoming,
            "stats": stats,
            "recent_payments": recent_payments,
            "enrollments": enrollments,
        },
    )


# ==================================================================
# Tickets
# ==================================================================
@ensure_csrf_cookie
@login_required(login_url="auth:login")
def tickets(request):
    """Tickets list (server-rendered) + AJAX create form."""
    tickets_qs = (
        request.user.tickets.order_by("-created_at")
    )
    return render(request, "accounts/tickets.html", {"tickets": tickets_qs})


@require_POST
@login_required(login_url="auth:login")
def ticket_create(request):
    """Create a ticket via AJAX. Returns JSON."""
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "errors": {"__all__": "بدنه درخواست نامعتبر است."}}, status=400)

    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    priority = data.get("priority") or Ticket.Priority.NORMAL
    category = data.get("category") or Ticket.Category.OTHER

    errors = {}
    if len(title) < 3:
        errors["title"] = "عنوان باید حداقل ۳ کاراکتر باشد."
    if len(description) < 10:
        errors["description"] = "متن درخواست باید حداقل ۱۰ کاراکتر باشد."
    if priority not in dict(Ticket.Priority.choices):
        errors["priority"] = "اولویت نامعتبر است."
    if category not in dict(Ticket.Category.choices):
        errors["category"] = "دسته‌بندی نامعتبر است."

    if errors:
        return JsonResponse({"ok": False, "errors": errors}, status=400)

    ticket = Ticket.objects.create(
        student=request.user,
        title=title,
        description=description,
        priority=priority,
        category=category,
        status=Ticket.Status.OPEN,
    )
    # Seed the first message with the description.
    TicketMessage.objects.create(ticket=ticket, sender=request.user, message=description)

    return JsonResponse({
        "ok": True,
        "ticket": _ticket_json(ticket),
    })


@login_required(login_url="auth:login")
def ticket_detail(request, pk):
    """Show a ticket and its thread. Only the owner can view."""
    ticket = get_object_or_404(Ticket, pk=pk, student=request.user)
    msgs = ticket.messages.select_related("sender").order_by("created_at")
    return render(
        request,
        "accounts/ticket_detail.html",
        {"ticket": ticket, "messages": msgs},
    )


@require_POST
@login_required(login_url="auth:login")
def ticket_reply(request, pk):
    """Reply to a ticket via AJAX. Returns JSON."""
    ticket = get_object_or_404(Ticket, pk=pk, student=request.user)
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "errors": {"message": "بدنه درخواست نامعتبر است."}}, status=400)

    message = (data.get("message") or "").strip()
    if len(message) < 2:
        return JsonResponse({"ok": False, "errors": {"message": "پیام نمی‌تواند خالی باشد."}}, status=400)

    msg = TicketMessage.objects.create(ticket=ticket, sender=request.user, message=message)
    # If the ticket was closed, reopen it on student reply.
    if ticket.status == Ticket.Status.CLOSED:
        ticket.status = Ticket.Status.OPEN
        ticket.save(update_fields=["status"])

    created = jdatetime.datetime.fromgregorian(datetime=msg.created_at).strftime("%H:%M - %d %B %Y")
    return JsonResponse({
        "ok": True,
        "message": {
            "body": msg.message,
            "sender_name": msg.sender.full_name if msg.sender else "سیستم",
            "is_me": True,
            "created_at_persian": created,
        },
    })


# ==================================================================
# Profile
# ==================================================================
@ensure_csrf_cookie
@login_required(login_url="auth:login")
def profile(request):
    """Edit basic profile + manage instruments (multi) + experiences."""
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "پروفایل شما با موفقیت به‌روزرسانی شد.")
            return redirect("auth:profile")
    else:
        form = ProfileForm(instance=request.user)

    from apps.accounts.models import Experience, InstrumentProfile, SkillLevel
    from apps.school.models import Instrument

    instrument_profiles = request.user.instrument_profiles.all()
    experiences = request.user.experiences.all()

    return render(
        request,
        "accounts/profile.html",
        {
            "form": form,
            "instrument_profiles": instrument_profiles,
            "experiences": experiences,
            "instrument_choices": Instrument.choices,
            "skill_level_choices": SkillLevel.choices,
            "experience_type_choices": Experience.Type.choices,
        },
    )


# ==================================================================
# Profile AJAX — add/remove instrument
# ==================================================================
@require_POST
@login_required(login_url="auth:login")
def profile_add_instrument(request):
    from apps.accounts.models import InstrumentProfile, SkillLevel
    from apps.school.models import Instrument

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "بدنه درخواست نامعتبر است."}, status=400)

    instrument = data.get("instrument", "").strip()
    skill_level = data.get("skill_level", SkillLevel.BEGINNER)
    started_year = data.get("started_year")
    is_primary = bool(data.get("is_primary", False))

    errors = {}
    if instrument not in dict(Instrument.choices):
        errors["instrument"] = "ساز نامعتبر است."
    if skill_level not in dict(SkillLevel.choices):
        errors["skill_level"] = "سطح نامعتبر است."
    if started_year:
        try:
            started_year = int(started_year)
            # Accept both Jalali (1300-1500) and Gregorian (1900-2100) years
            if not (1300 <= started_year <= 1500 or 1900 <= started_year <= 2100):
                errors["started_year"] = "سال نامعتبر است."
        except (TypeError, ValueError):
            errors["started_year"] = "سال باید عدد باشد."

    if errors:
        return JsonResponse({"ok": False, "errors": errors}, status=400)

    if InstrumentProfile.objects.filter(user=request.user, instrument=instrument).exists():
        return JsonResponse(
            {"ok": False, "error": "این ساز قبلاً برای شما ثبت شده است."}, status=400
        )

    # If marking as primary, unmark others.
    if is_primary:
        InstrumentProfile.objects.filter(user=request.user, is_primary=True).update(is_primary=False)

    # First instrument is automatically primary if none exists yet.
    if not request.user.instrument_profiles.exists():
        is_primary = True

    profile = InstrumentProfile.objects.create(
        user=request.user,
        instrument=instrument,
        skill_level=skill_level,
        started_year=started_year or None,
        is_primary=is_primary,
    )
    return JsonResponse({
        "ok": True,
        "instrument_profile": {
            "id": profile.id,
            "instrument": profile.instrument,
            "instrument_label": profile.get_instrument_display(),
            "skill_level": profile.skill_level,
            "skill_level_label": profile.get_skill_level_display(),
            "started_year": profile.started_year,
            "is_primary": profile.is_primary,
        },
    })


@require_POST
@login_required(login_url="auth:login")
def profile_remove_instrument(request, pk):
    from apps.accounts.models import InstrumentProfile

    profile = get_object_or_404(InstrumentProfile, pk=pk, user=request.user)
    was_primary = profile.is_primary
    profile.delete()
    # Promote another to primary if needed.
    if was_primary:
        first = request.user.instrument_profiles.first()
        if first:
            first.is_primary = True
            first.save(update_fields=["is_primary"])
    return JsonResponse({"ok": True})


# ==================================================================
# Profile AJAX — add/remove experience
# ==================================================================
@require_POST
@login_required(login_url="auth:login")
def profile_add_experience(request):
    from apps.accounts.models import Experience

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "بدنه درخواست نامعتبر است."}, status=400)

    title = (data.get("title") or "").strip()
    experience_type = data.get("experience_type", Experience.Type.OTHER)
    description = (data.get("description") or "").strip()
    event_date = data.get("event_date") or None
    location = (data.get("location") or "").strip()

    errors = {}
    if len(title) < 3:
        errors["title"] = "عنوان باید حداقل ۳ کاراکتر باشد."
    if experience_type not in dict(Experience.Type.choices):
        errors["experience_type"] = "نوع نامعتبر است."

    if errors:
        return JsonResponse({"ok": False, "errors": errors}, status=400)

    # Parse event_date string to a date object if provided
    from datetime import date as date_cls
    parsed_date = None
    if event_date:
        try:
            parsed_date = date_cls.fromisoformat(event_date)
        except (TypeError, ValueError):
            pass

    exp = Experience.objects.create(
        user=request.user,
        title=title,
        experience_type=experience_type,
        description=description,
        event_date=parsed_date,
        location=location,
    )
    date_persian = ""
    if exp.event_date:
        try:
            date_persian = jdatetime.date.fromgregorian(date=exp.event_date).strftime("%d %B %Y")
        except Exception:
            date_persian = str(exp.event_date)
    return JsonResponse({
        "ok": True,
        "experience": {
            "id": exp.id,
            "title": exp.title,
            "experience_type": exp.experience_type,
            "experience_type_label": exp.get_experience_type_display(),
            "description": exp.description,
            "event_date": exp.event_date.isoformat() if exp.event_date else "",
            "event_date_persian": date_persian,
            "location": exp.location,
        },
    })


@require_POST
@login_required(login_url="auth:login")
def profile_remove_experience(request, pk):
    from apps.accounts.models import Experience

    exp = get_object_or_404(Experience, pk=pk, user=request.user)
    exp.delete()
    return JsonResponse({"ok": True})


# ==================================================================
# Helpers
# ==================================================================
def _ticket_json(ticket: Ticket) -> dict:
    return {
        "id": ticket.id,
        "title": ticket.title,
        "description": ticket.description,
        "priority": ticket.priority,
        "category": ticket.category,
        "status": ticket.status,
        "priority_label": ticket.get_priority_display(),
        "category_label": ticket.get_category_display(),
        "status_label": ticket.get_status_display(),
        "created_at_persian": jdatetime.datetime.fromgregorian(
            datetime=ticket.created_at
        ).strftime("%d %B %Y - %H:%M"),
        "url": reverse("auth:ticket_detail", args=[ticket.id]),
    }
