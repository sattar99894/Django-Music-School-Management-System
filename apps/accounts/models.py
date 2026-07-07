"""
User model — extended with profile fields for the Music School.

Authentication uses the Iranian mobile phone number as the unique
identifier (no `username` field). One model serves students, teachers
and admins, distinguished by the `role` field.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from .managers import CustomUserManager


class User(AbstractUser):
    # ----- Choices -----
    class Role(models.TextChoices):
        STUDENT = "STUDENT", _("دانشجو")
        TEACHER = "TEACHER", _("مدرس")
        ADMIN = "ADMIN", _("مدیر")

    class SkillLevel(models.TextChoices):
        BEGINNER = "BEGINNER", _("مقدماتی")
        INTERMEDIATE = "INTERMEDIATE", _("متوسط")
        ADVANCED = "ADVANCED", _("پیشرفته")

    # Drop the default `username` — log in with phone.
    username = None

    phone = models.CharField(_("شماره موبایل"), max_length=11, unique=True)
    national_id = models.CharField(
        _("کد ملی"), max_length=10, unique=True, null=True, blank=True
    )
    full_name = models.CharField(_("نام و نام خانوادگی"), max_length=150, blank=True)
    email = models.EmailField(_("ایمیل"), blank=True)

    role = models.CharField(
        _("نقش"), max_length=10, choices=Role.choices, default=Role.STUDENT
    )

    # Student profile extras
    instrument = models.CharField(_("ساز اصلی"), max_length=50, blank=True)
    skill_level = models.CharField(
        _("سطح هنری"), max_length=12, choices=SkillLevel.choices, blank=True
    )
    avatar = models.ImageField(
        _("تصویر پروفایل"), upload_to="avatars/", blank=True, null=True
    )

    created_at = models.DateTimeField(_("تاریخ عضویت"), auto_now_add=True)
    updated_at = models.DateTimeField(_("آخرین به‌روزرسانی"), auto_now=True)

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["full_name"]

    objects = CustomUserManager()

    class Meta:
        verbose_name = _("کاربر")
        verbose_name_plural = _("کاربران")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.full_name or self.phone

    @property
    def is_student(self) -> bool:
        return self.role == self.Role.STUDENT

    @property
    def is_teacher(self) -> bool:
        return self.role == self.Role.TEACHER

    @property
    def is_admin_role(self) -> bool:
        return self.role == self.Role.ADMIN
