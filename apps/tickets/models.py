"""
Support ticket system — students open tickets, admins/staff reply.

    User (student) ──1:N── Ticket ──1:N── TicketMessage ──N:1── User (sender)
"""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Ticket(models.Model):
    class Priority(models.TextChoices):
        LOW = "LOW", _("کم")
        NORMAL = "NORMAL", _("معمولی")
        HIGH = "HIGH", _("زیاد")
        URGENT = "URGENT", _("فوری")

    class Category(models.TextChoices):
        FINANCE = "FINANCE", _("مالی و پرداخت")
        CLASS = "CLASS", _("کلاس و دوره")
        SCHEDULE = "SCHEDULE", _("برنامه کلاسی")
        OTHER = "OTHER", _("سایر")

    class Status(models.TextChoices):
        OPEN = "OPEN", _("باز")
        ANSWERED = "ANSWERED", _("پاسخ داده‌شده")
        CLOSED = "CLOSED", _("بسته‌شده")

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="tickets", verbose_name=_("دانشجو"),
    )
    title = models.CharField(_("عنوان"), max_length=200)
    description = models.TextField(_("متن درخواست"))
    priority = models.CharField(
        _("اولویت"), max_length=10, choices=Priority.choices, default=Priority.NORMAL
    )
    category = models.CharField(
        _("دسته‌بندی"), max_length=10, choices=Category.choices, default=Category.OTHER
    )
    status = models.CharField(
        _("وضعیت"), max_length=10, choices=Status.choices, default=Status.OPEN
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("تیکت")
        verbose_name_plural = _("تیکت‌ها")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title


class TicketMessage(models.Model):
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name="messages",
        verbose_name=_("تیکت"),
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="ticket_messages", verbose_name=_("فرستنده"),
    )
    message = models.TextField(_("پیام"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("پیام تیکت")
        verbose_name_plural = _("پیام‌های تیکت")
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"پیام در {self.ticket_id}"
