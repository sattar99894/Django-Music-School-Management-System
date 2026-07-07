"""
Payment views — Zarinpal request & verify.

`zarinpal_request`: redirects the student to the Zarinpal hosted page.
`zarinpal_verify` : the callback. Verifies the payment, marks it
                    SUCCESS/FAILED, stores the ref_id, and on success
                    auto-creates the student's Enrollment and logs them in.
"""
from django.contrib.auth import login
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib import messages

from apps.payments.models import Payment
from apps.school.models import Class, Enrollment
from . import zarinpal


def zarinpal_request(request, payment_id):
    """Redirect the student to the Zarinpal hosted payment page."""
    payment = get_object_or_404(Payment, pk=payment_id, status=Payment.Status.PENDING)

    callback_url = request.build_absolute_uri(reverse("payments:zarinpal_verify"))
    description = f"ثبت‌نام دوره — هنرستان موسیقی شیراز (پرداخت #{payment.pk})"

    try:
        authority, gateway_url = zarinpal.request_payment(
            amount=payment.amount,
            description=description,
            callback_url=callback_url,
        )
    except zarinpal.ZarinpalError as exc:
        payment.status = Payment.Status.FAILED
        payment.save(update_fields=["status"])
        messages.error(request, str(exc))
        return redirect("core:course_detail", pk=payment.course_id)

    payment.authority = authority
    payment.save(update_fields=["authority"])
    return redirect(gateway_url)


def zarinpal_verify(request):
    """
    Zarinpal callback.

    GET params: Status (OK/NOK), Authority.

    On success:
        * verify the payment with the gateway
        * set Payment.status = SUCCESS, store ref_id
        * create an Enrollment in the course's first active class
        * auto-login the student and show the success page (RefID)
    On failure:
        * set Payment.status = FAILED and show the fail page
    """
    status = request.GET.get("Status", "")
    authority = request.GET.get("Authority", "")

    if not authority:
        return render(request, "payments/verify_fail.html", {"message": "پارامتر Authority یافت نشد."})

    payment = get_object_or_404(Payment, authority=authority)

    # Idempotency — if already verified (e.g. page refresh), just show success.
    if payment.status == Payment.Status.SUCCESS:
        return render(
            request,
            "payments/verify_success.html",
            {"payment": payment, "ref_id": payment.ref_id, "already_verified": True},
        )

    # Zarinpal reported the user cancelled / failed before paying.
    if status != "OK":
        payment.status = Payment.Status.FAILED
        payment.save(update_fields=["status"])
        return render(
            request,
            "payments/verify_fail.html",
            {"payment": payment, "message": "پرداخت توسط کاربر لغو شد یا ناموفق بود."},
        )

    # Verify with the gateway.
    success, ref_id, message = zarinpal.verify_payment(authority, payment.amount)

    if not success:
        payment.status = Payment.Status.FAILED
        payment.save(update_fields=["status"])
        return render(
            request,
            "payments/verify_fail.html",
            {"payment": payment, "message": message},
        )

    # ---- SUCCESS ----
    payment.status = Payment.Status.SUCCESS
    payment.ref_id = ref_id
    payment.save(update_fields=["status", "ref_id"])

    # Auto-enrol the student in the course's first active class.
    enrolled_class = None
    if payment.course_id:
        enrolled_class = (
            Class.objects.filter(
                course_id=payment.course_id, status=Class.Status.ACTIVE
            )
            .order_by("created_at")
            .first()
        )
        if enrolled_class:
            Enrollment.objects.get_or_create(
                student=payment.student,
                class_ref=enrolled_class,
                defaults={
                    "term": enrolled_class.term,
                    "status": Enrollment.Status.ENROLLED,
                },
            )

    # Auto-login the student (covers guest checkout).
    if not request.user.is_authenticated:
        login(request, payment.student)

    return render(
        request,
        "payments/verify_success.html",
        {"payment": payment, "ref_id": ref_id, "enrolled_class": enrolled_class},
    )
