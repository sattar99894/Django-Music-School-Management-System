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
    if request.user.is_authenticated:
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
        return redirect("auth:admin_dashboard")

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
@login_required(login_url="auth:login")
def profile(request):
    """Edit profile fields + upload avatar."""
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "پروفایل شما با موفقیت به‌روزرسانی شد.")
            return redirect("auth:profile")
    else:
        form = ProfileForm(instance=request.user)

    return render(request, "accounts/profile.html", {"form": form})


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
