"""
User model — extended with profile fields for the Music School.

Authentication uses the Iranian mobile phone number as the unique
identifier (no `username` field). One model serves students, teachers
and admins, distinguished by the `role` field.

A user can play **multiple instruments**, each at its own skill level
(see :model:`accounts.InstrumentProfile`) and have a list of
**experiences** such as event/competition participation
(see :model:`accounts.Experience`).
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.school.models import Instrument

from .managers import CustomUserManager


class User(AbstractUser):
    # ----- Choices -----
    class Role(models.TextChoices):
        STUDENT = "STUDENT", _("دانشجو")
        TEACHER = "TEACHER", _("مدرس")
        ADMIN = "ADMIN", _("مدیر")

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

    @property
    def primary_instrument_profile(self):
        """Return the user's primary InstrumentProfile, or the first one."""
        qs = self.instrument_profiles.all()
        return qs.filter(is_primary=True).first() or qs.first()


# ------------------------------------------------------------------
# Skill levels — 5 tiers (shared by InstrumentProfile and Course)
# ------------------------------------------------------------------
class SkillLevel(models.TextChoices):
    BEGINNER = "BEGINNER", _("مقدماتی")
    ELEMENTARY = "ELEMENTARY", _("ابتدایی")
    INTERMEDIATE = "INTERMEDIATE", _("متوسط")
    ADVANCED = "ADVANCED", _("پیشرفته")
    PROFESSIONAL = "PROFESSIONAL", _("حرفه‌ای")


# ------------------------------------------------------------------
# InstrumentProfile — one user can play many instruments, each at its
# own skill level.
# ------------------------------------------------------------------
class InstrumentProfile(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="instrument_profiles",
        verbose_name=_("کاربر"),
    )
    instrument = models.CharField(
        _("ساز"), max_length=20, choices=Instrument.choices,
        blank=True,null=True,
    )
    skill_level = models.CharField(
        _("سطح"), max_length=15, choices=SkillLevel.choices,
        default=SkillLevel.BEGINNER,
    )
    started_year = models.PositiveIntegerField(_("سال شروع"), null=True, blank=True)
    is_primary = models.BooleanField(_("ساز اصلی"), default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("ساز کاربر")
        verbose_name_plural = _("سازهای کاربران")
        unique_together = [("user", "instrument")]
        ordering = ["-is_primary", "instrument"]

    def __str__(self) -> str:
        return f"{self.user} — {self.get_instrument_display()}"

    def label(self) -> str:
        """Human label e.g. «پیانو (پیشرفته)»"""
        return f"{self.get_instrument_display()} ({self.get_skill_level_display()})"


# ------------------------------------------------------------------
# Experience — student/teacher résumé entries: concerts, orchestras,
# competitions, certificates, etc.
# ------------------------------------------------------------------
class Experience(models.Model):
    class Type(models.TextChoices):
        EVENT = "EVENT", _("رویداد")
        ORCHESTRA = "ORCHESTRA", _("ارکستر")
        PERFORMANCE = "PERFORMANCE", _("اجرا")
        COMPETITION = "COMPETITION", _("مسابقه")
        CERTIFICATE = "CERTIFICATE", _("گواهینامه")
        OTHER = "OTHER", _("سایر")

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="experiences",
        verbose_name=_("کاربر"),
    )
    title = models.CharField(_("عنوان"), max_length=200)
    experience_type = models.CharField(
        _("نوع سابقه"), max_length=15, choices=Type.choices,
        default=Type.PERFORMANCE,
    )
    description = models.TextField(_("توضیحات"), blank=True)
    event_date = models.DateField(_("تاریخ"), null=True, blank=True)
    location = models.CharField(_("مکان"), max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("سابقه")
        verbose_name_plural = _("سوابق")
        ordering = ["-event_date", "-created_at"]

    def __str__(self) -> str:
        return f"{self.user} — {self.title}"
