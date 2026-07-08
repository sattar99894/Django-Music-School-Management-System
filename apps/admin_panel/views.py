"""
Admin panel views — dashboard, classes management, and the
students & teachers directory.

All views require an authenticated admin (`@admin_required`).
AJAX endpoints return JSON or HTML fragments.
"""
import json

import jdatetime
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from apps.accounts.decorators import admin_required
from apps.accounts.models import User
from apps.payments.models import Payment
from apps.school.models import Class, Course, Enrollment, Instrument, Teacher
from apps.tickets.models import Ticket

# Instrument label lookup (User.instrument is a plain CharField, not a choices field)
_INSTRUMENT_LABELS = dict(Instrument.choices)


# ==================================================================
# Helpers
# ==================================================================
def _jalali_month_range(year: int, month: int):
    """Return (start_greg, end_greg) datetimes for a Jalali month."""
    start_jd = jdatetime.date(year, month, 1)
    if month == 12:
        end_jd = jdatetime.date(year + 1, 1, 1)
    else:
        end_jd = jdatetime.date(year, month + 1, 1)
    return start_jd.togregorian(), end_jd.togregorian()


def _revenue_for_month(year: int, month: int) -> int:
    start, end = _jalali_month_range(year, month)
    return (
        Payment.objects.filter(
            status=Payment.Status.SUCCESS, created_at__gte=start, created_at__lt=end
        ).aggregate(t=Sum("amount"))["t"]
        or 0
    )


def _revenue_trend(months: int = 6):
    """Last N Jalali months of successful revenue (oldest first)."""
    now = jdatetime.datetime.now()
    trend = []
    for i in range(months - 1, -1, -1):
        y, m = now.year, now.month - i
        while m <= 0:
            m += 12
            y -= 1
        trend.append({
            "label": jdatetime.date(y, m, 1).strftime("%B"),
            "total": _revenue_for_month(y, m),
            "year": y,
            "month": m,
        })
    return trend


# ==================================================================
# Dashboard
# ==================================================================
@admin_required
def dashboard(request):
    now = jdatetime.datetime.now()

    total_students = User.objects.filter(role=User.Role.STUDENT).count()
    active_classes = Class.objects.filter(status=Class.Status.ACTIVE).count()
    monthly_revenue = _revenue_for_month(now.year, now.month)
    pending_tickets = Ticket.objects.filter(
        status__in=[Ticket.Status.OPEN, Ticket.Status.ANSWERED]
    ).count()

    total_revenue = (
        Payment.objects.filter(status=Payment.Status.SUCCESS).aggregate(
            t=Sum("amount")
        )["t"]
        or 0
    )

    trend = _revenue_trend(6)
    max_trend = max((t["total"] for t in trend), default=1) or 1

    recent_enrollments = (
        Enrollment.objects.select_related("student", "class_ref__course")
        .order_by("-created_at")[:5]
    )
    recent_payments = (
        Payment.objects.select_related("student", "course").order_by("-created_at")[:5]
    )
    recent_tickets = (
        Ticket.objects.select_related("student").order_by("-created_at")[:5]
    )

    stats = {
        "total_students": total_students,
        "active_classes": active_classes,
        "monthly_revenue": monthly_revenue,
        "pending_tickets": pending_tickets,
        "total_teachers": Teacher.objects.count(),
        "total_courses": Course.objects.count(),
        "total_revenue": total_revenue,
        "total_enrollments": Enrollment.objects.filter(
            status=Enrollment.Status.ENROLLED
        ).count(),
    }

    return render(
        request,
        "admin_panel/dashboard.html",
        {
            "stats": stats,
            "trend": trend,
            "max_trend": max_trend,
            "current_jalali_month": now.strftime("%B %Y"),
            "recent_enrollments": recent_enrollments,
            "recent_payments": recent_payments,
            "recent_tickets": recent_tickets,
        },
    )


# ==================================================================
# Classes management
# ==================================================================
@admin_required
def classes_list(request):
    classes = (
        Class.objects.select_related("course", "teacher__user")
        .annotate(
            active_enrollments=Count(
                "enrollments", filter=Q(enrollments__status=Enrollment.Status.ENROLLED)
            )
        )
        .order_by("-created_at")
    )

    term = request.GET.get("term", "")
    status = request.GET.get("status", "")
    if term:
        classes = classes.filter(term=term)
    if status:
        classes = classes.filter(status=status)

    terms = list(Class.objects.values_list("term", flat=True).distinct().order_by("term"))

    return render(
        request,
        "admin_panel/classes.html",
        {"classes": classes, "terms": terms, "filters": {"term": term, "status": status}},
    )


@admin_required
def class_detail(request, pk):
    cls = get_object_or_404(
        Class.objects.select_related("course", "teacher__user"), pk=pk
    )
    enrollments = cls.enrollments.select_related("student").order_by(
        "student__full_name"
    )
    return render(
        request,
        "admin_panel/class_detail.html",
        {"cls": cls, "enrollments": enrollments},
    )


@require_POST
@admin_required
def class_add_student(request, pk):
    """Add a student to a class via AJAX."""
    cls = get_object_or_404(Class, pk=pk)
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "بدنه درخواست نامعتبر است."}, status=400)

    student_id = data.get("student_id")
    student = get_object_or_404(User, pk=student_id, role=User.Role.STUDENT)

    enrollment, created = Enrollment.objects.get_or_create(
        student=student,
        class_ref=cls,
        defaults={"term": cls.term, "status": Enrollment.Status.ENROLLED},
    )

    if not created:
        if enrollment.status == Enrollment.Status.DROPPED:
            enrollment.status = Enrollment.Status.ENROLLED
            enrollment.save(update_fields=["status"])
            return JsonResponse({"ok": True, "message": "دانشجو مجدداً در کلاس ثبت شد."})
        return JsonResponse(
            {"ok": False, "error": "این دانشجو قبلاً در این کلاس ثبت‌نام شده است."},
            status=400,
        )

    return JsonResponse({
        "ok": True,
        "message": "دانشجو با موفقیت به کلاس اضافه شد.",
        "enrollment": {
            "id": enrollment.id,
            "student_id": student.id,
            "student_name": student.full_name or student.phone,
            "student_phone": student.phone,
            "term": enrollment.term,
            "status": enrollment.status,
            "status_label": enrollment.get_status_display(),
            "detail_url": reverse("admin_panel:student_detail", args=[student.id]),
            "remove_url": reverse("admin_panel:class_remove_student", args=[cls.id, enrollment.id]),
        },
    })


@require_POST
@admin_required
def class_remove_student(request, pk, enrollment_id):
    """Drop a student from a class via AJAX (sets status=DROPPED)."""
    enrollment = get_object_or_404(Enrollment, pk=enrollment_id, class_ref_id=pk)
    enrollment.status = Enrollment.Status.DROPPED
    enrollment.save(update_fields=["status"])
    return JsonResponse({"ok": True, "message": "دانشجو از کلاس حذف شد."})


@require_GET
@admin_required
def student_search(request):
    """AJAX student search for the 'add to class' modal."""
    q = request.GET.get("q", "").strip()
    exclude_class = request.GET.get("exclude_class")
    qs = User.objects.filter(role=User.Role.STUDENT)
    if q:
        qs = qs.filter(
            Q(full_name__icontains=q) | Q(phone__icontains=q) | Q(national_id__icontains=q)
        )
    if exclude_class:
        qs = qs.exclude(
            enrollments__class_ref_id=exclude_class,
            enrollments__status=Enrollment.Status.ENROLLED,
        )
    students = qs.order_by("full_name")[:15]
    result = []
    for s in students:
        primary = s.instrument_profiles.filter(is_primary=True).first() or s.instrument_profiles.first()
        instruments_str = "، ".join(
            ip.get_instrument_display() for ip in s.instrument_profiles.all()[:3]
        ) or "—"
        result.append({
            "id": s.id,
            "full_name": s.full_name or "(بدون نام)",
            "phone": s.phone,
            "instrument": _INSTRUMENT_LABELS.get(primary.instrument, primary.instrument) if primary else "—",
            "instruments": instruments_str,
        })
    return JsonResponse({"ok": True, "students": result})


# ==================================================================
# Students & Teachers directory
# ==================================================================
@admin_required
def directory(request):
    role = request.GET.get("role", "STUDENT")
    if role not in ("STUDENT", "TEACHER"):
        role = "STUDENT"

    q = request.GET.get("q", "").strip()
    skill_level = request.GET.get("skill_level", "")
    instrument = request.GET.get("instrument", "")
    sort = request.GET.get("sort", "name_asc")
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")

    qs = User.objects.filter(role=role).distinct()
    if role == "TEACHER":
        qs = qs.select_related("teacher_profile")

    if q:
        qs = qs.filter(
            Q(full_name__icontains=q)
            | Q(phone__icontains=q)
            | Q(national_id__icontains=q)
        )
    if skill_level:
        qs = qs.filter(instrument_profiles__skill_level=skill_level).distinct()
    if instrument:
        qs = qs.filter(instrument_profiles__instrument=instrument).distinct()
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    if sort == "date_desc":
        qs = qs.order_by("-created_at")
    elif sort == "date_asc":
        qs = qs.order_by("created_at")
    elif sort == "name_desc":
        qs = qs.order_by("-full_name")
    else:  # name_asc — Persian alphabetical (approximate via DB collation)
        qs = qs.order_by("full_name")

    users = list(qs)

    # For Persian alphabetical sort, normalize Arabic variants and re-sort in Python.
    if sort in ("name_asc", "name_desc"):
        repl = str.maketrans({"ي": "ی", "ك": "ک", "أ": "ا", "إ": "ا", "ؤ": "و", "ئ": "ی"})
        users.sort(
            key=lambda u: (u.full_name or "").translate(repl).lower(),
            reverse=(sort == "name_desc"),
        )

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.GET.get("ajax")

    filters = {
        "role": role,
        "q": q,
        "skill_level": skill_level,
        "instrument": instrument,
        "sort": sort,
        "date_from": date_from,
        "date_to": date_to,
    }

    if is_ajax:
        return render(
            request,
            "admin_panel/_directory_rows.html",
            {"users": users, "role": role},
        )

    return render(
        request,
        "admin_panel/directory.html",
        {
            "users": users,
            "role": role,
            "filters": filters,
            "instruments_choices": Instrument.choices,
        },
    )


# ==================================================================
# Student / Teacher detail
# ==================================================================
@admin_required
def student_detail(request, pk):
    user_obj = get_object_or_404(
        User, pk=pk, role__in=[User.Role.STUDENT, User.Role.TEACHER]
    )
    enrollments = (
        user_obj.enrollments.select_related(
            "class_ref__course", "class_ref__teacher__user"
        ).order_by("-created_at")
    )
    payments = user_obj.payments.select_related("course").order_by("-created_at")
    tickets = user_obj.tickets.order_by("-created_at")
    instrument_profiles = user_obj.instrument_profiles.all()
    experiences = user_obj.experiences.all()

    teacher_profile = getattr(user_obj, "teacher_profile", None) if user_obj.role == User.Role.TEACHER else None

    return render(
        request,
        "admin_panel/student_detail.html",
        {
            "user_obj": user_obj,
            "enrollments": enrollments,
            "payments": payments,
            "tickets": tickets,
            "instrument_profiles": instrument_profiles,
            "experiences": experiences,
            "teacher_profile": teacher_profile,
        },
    )
