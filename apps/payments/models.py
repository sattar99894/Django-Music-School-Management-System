"""
Payment records for the Zarinpal gateway.

Lifecycle:
    PENDING  -> created when the student submits the invoice form
    SUCCESS  -> set after a successful verify (ref_id populated)
    FAILED   -> set if the user cancels or verify fails
"""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", _("در انتظار")
        SUCCESS = "SUCCESS", _("موفق")
        FAILED = "FAILED", _("ناموفق")

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="payments", verbose_name=_("دانشجو"),
    )
    course = models.ForeignKey(
        "school.Course", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="payments", verbose_name=_("دوره"),
    )
    amount = models.PositiveIntegerField(_("مبلغ (تومان)"))
    authority = models.CharField(_("Authority"), max_length=100, blank=True)
    ref_id = models.CharField(_("RefID"), max_length=100, blank=True)
    status = models.CharField(
        _("وضعیت"), max_length=10, choices=Status.choices, default=Status.PENDING
    )
    description = models.CharField(_("توضیحات"), max_length=255, blank=True)

    # Snapshot of student info at payment time (useful for guest checkouts)
    student_name = models.CharField(_("نام دانشجو"), max_length=150, blank=True)
    student_phone = models.CharField(_("موبایل دانشجو"), max_length=11, blank=True)
    student_national_id = models.CharField(_("کد ملی دانشجو"), max_length=10, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("پرداخت")
        verbose_name_plural = _("پرداخت‌ها")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"پرداخت #{self.pk} — {self.amount} تومان — {self.get_status_display()}"
