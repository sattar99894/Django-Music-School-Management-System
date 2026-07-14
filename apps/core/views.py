"""
Public website views — landing page, courses list, course detail,
and the invoice / checkout page that starts the Zarinpal flow.
"""
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from apps.accounts.models import User
from apps.payments.models import Payment
from apps.school.models import Course
from django.contrib.auth.decorators import login_required


# ------------------------------------------------------------------
# Landing page
# ------------------------------------------------------------------
def landing(request):
    courses = (
        Course.objects.filter(is_active=True)
        .select_related("teacher", "teacher__user")
        .order_by("-created_at")[:6]
    )
    return render(request, "core/landing.html", {"courses": courses})


# ------------------------------------------------------------------
# Courses list
# ------------------------------------------------------------------
def course_list(request):
    courses = (
        Course.objects.filter(is_active=True)
        .select_related("teacher", "teacher__user")
        .order_by("title")
    )
    return render(request, "core/course_list.html", {"courses": courses})


# ------------------------------------------------------------------
# Course detail
# ------------------------------------------------------------------
def course_detail(request, pk):
    course = get_object_or_404(
        Course.objects.select_related("teacher", "teacher__user"), pk=pk
    )
    classes = course.classes.all().order_by("-created_at")
    return render(request, "core/course_detail.html", {"course": course, "classes": classes})


# ------------------------------------------------------------------
# Invoice / checkout
# ------------------------------------------------------------------
@login_required(login_url="auth:login")
@require_http_methods(["GET", "POST"])
def invoice(request, course_id):
    course = get_object_or_404(Course, pk=course_id)

    if request.method == "POST":
        # Authenticated students reuse their own account; guests fill the form.
        if request.user.is_authenticated and request.user.role != User.Role.ADMIN:
            student = request.user
            # keep snapshot info fresh
            if not student.national_id:
                student.national_id = request.POST.get("national_id", "").strip() or None
                student.save(update_fields=["national_id"])
            full_name = student.full_name
            phone = student.phone
            national_id = student.national_id or ""
        else:
            full_name = request.POST.get("full_name", "").strip()
            phone = request.POST.get("phone", "").strip()
            national_id = request.POST.get("national_id", "").strip()

            errors = []
            if len(full_name) < 3:
                errors.append("نام و نام خانوادگی را به‌صورت کامل وارد کنید.")
            if not (phone.startswith("09") and len(phone) == 11 and phone.isdigit()):
                errors.append("شماره موبایل باید ۱۱ رقمی و با ۰۹ شروع شود.")
            if not (national_id.isdigit() and len(national_id) == 10):
                errors.append("کد ملی باید ۱۰ رقم باشد.")

            if errors:
                return render(
                    request,
                    "core/invoice.html",
                    {"course": course, "errors": errors, "form": request.POST},
                )

            student = User.objects.filter(phone=phone).first()
            if student is None:
                student = User.objects.create_user(
                    phone=phone,
                    full_name=full_name,
                    password=national_id or User.objects.make_random_password(),
                    role=User.Role.STUDENT,
                    national_id=national_id or None,
                )
            else:
                if not student.full_name:
                    student.full_name = full_name
                if national_id and not student.national_id:
                    student.national_id = national_id
                student.save()

        payment = Payment.objects.create(
            student=student,
            course=course,
            amount=course.price,
            status=Payment.Status.PENDING,
            description=f"ثبت‌نام دوره «{course.title}»",
            student_name=full_name,
            student_phone=phone,
            student_national_id=national_id,
        )
        return redirect("payments:zarinpal_request", payment_id=payment.id)

    # GET — prefill for authenticated students
    initial = None
    if request.user.is_authenticated and request.user.role != User.Role.ADMIN:
        initial = {
            "full_name": request.user.full_name,
            "phone": request.user.phone,
            "national_id": request.user.national_id or "",
        }
    return render(
        request,
        "core/invoice.html",
        {"course": course, "errors": [], "form": initial},
    )
