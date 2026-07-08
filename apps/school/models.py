"""
School domain models — the heart of the academy.

    User (role=TEACHER) ──1:1── Teacher ──1:N── Course ──1:N── Class ──1:N── Enrollment ──N:1── User (role=STUDENT)

A *Course* is a catalog offering (e.g. "دوره پیانو مقدماتی").
A *Class*  is a concrete scheduled offering of a course for a term.
An *Enrollment* ties a student to a class.
"""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


# ------------------------------------------------------------------
# Instrument choices — centralised so filters & forms stay in sync.
# ------------------------------------------------------------------
class Instrument(models.TextChoices):
    PIANO = "PIANO", _("پیانو")
    GUITAR = "GUITAR", _("گیتار")
    VIOLIN = "VIOLIN", _("ویولن")
    TAR = "TAR", _("تار")
    SETAR = "SETAR", _("سه‌تار")
    SANTUR = "SANTUR", _("سنتور")
    FLUTE = "FLUTE", _("فلوت")
    NEY = "NEY", _("نی")
    UD = "UD", _("عود")
    KAMANCHEH = "KAMANCHEH", _("کمانچه")
    DAF = "DAF", _("دف")
    TOMBAK = "TOMBAK", _("تمبک")
    VOCAL = "VOCAL", _("آواز")


class SkillLevel(models.TextChoices):
    BEGINNER = "BEGINNER", _("مقدماتی")
    ELEMENTARY = "ELEMENTARY", _("ابتدایی")
    INTERMEDIATE = "INTERMEDIATE", _("متوسط")
    ADVANCED = "ADVANCED", _("پیشرفته")
    PROFESSIONAL = "PROFESSIONAL", _("حرفه‌ای")


# ------------------------------------------------------------------
# Teacher — 1:1 extension of a User with role=TEACHER
# ------------------------------------------------------------------
class Teacher(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_profile",
        verbose_name=_("حساب کاربری"),
    )
    bio = models.TextField(_("شرح حال"), blank=True)
    specialty = models.CharField(_("تخصص"), max_length=200, blank=True)
    experience_years = models.PositiveIntegerField(_("سال‌های تجربه"), default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("مدرس")
        verbose_name_plural = _("مدرسین")
        ordering = ["user__full_name"]

    def __str__(self) -> str:
        return self.user.full_name or self.user.phone


# ------------------------------------------------------------------
# Course — catalog offering
# ------------------------------------------------------------------
class Course(models.Model):
    title = models.CharField(_("عنوان دوره"), max_length=200)
    slug = models.SlugField(_("نامک"), max_length=220, unique=True, allow_unicode=True)
    description = models.TextField(_("توضیحات"))
    price = models.PositiveIntegerField(_("شهریه (تومان)"))
    duration_weeks = models.PositiveIntegerField(_("مدت دوره (هفته)"), default=12)
    level = models.CharField(
        _("سطح"), max_length=15, choices=SkillLevel.choices, default=SkillLevel.BEGINNER
    )
    instrument = models.CharField(
        _("ساز"), max_length=20, choices=Instrument.choices
    )
    teacher = models.ForeignKey(
        Teacher, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="courses", verbose_name=_("مدرس"),
    )
    image = models.URLField(_("تصویر دوره"), blank=True)
    is_active = models.BooleanField(_("فعال"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("دوره")
        verbose_name_plural = _("دوره‌ها")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title


# ------------------------------------------------------------------
# Class — concrete scheduled offering of a Course for a term.
# `schedule` is JSON: {"شنبه": "16:00-17:30", "دوشنبه": "16:00-17:30"}
# ------------------------------------------------------------------
class Class(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", _("فعال")
        ENDED = "ENDED", _("پایان‌یافته")
        CANCELED = "CANCELED", _("لغو‌شده")

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="classes", verbose_name=_("دوره")
    )
    teacher = models.ForeignKey(
        Teacher, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="classes", verbose_name=_("مدرس کلاس"),
    )
    term = models.CharField(_("ترم"), max_length=100, default="پاییز ۱۴۰۳")
    schedule = models.JSONField(_("برنامه هفتگی"), default=dict, blank=True)
    capacity = models.PositiveIntegerField(_("ظرفیت"), default=12)
    start_date = models.DateField(_("تاریخ شروع"), null=True, blank=True)
    end_date = models.DateField(_("تاریخ پایان"), null=True, blank=True)
    status = models.CharField(
        _("وضعیت"), max_length=10, choices=Status.choices, default=Status.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("کلاس")
        verbose_name_plural = _("کلاس‌ها")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.course.title} — {self.term}"

    @property
    def enrolled_count(self) -> int:
        return self.enrollments.filter(status=Enrollment.Status.ENROLLED).count()

    @property
    def is_full(self) -> bool:
        return self.enrolled_count >= self.capacity


# ------------------------------------------------------------------
# Enrollment — Student (User) ↔ Class
# ------------------------------------------------------------------
class Enrollment(models.Model):
    class Status(models.TextChoices):
        ENROLLED = "ENROLLED", _("ثبت‌نام‌شده")
        DROPPED = "DROPPED", _("انصرافی")
        COMPLETED = "COMPLETED", _("تکمیل‌شده")

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="enrollments", verbose_name=_("دانشجو"),
    )
    class_ref = models.ForeignKey(
        Class, on_delete=models.CASCADE, related_name="enrollments",
        verbose_name=_("کلاس"),
    )
    term = models.CharField(_("ترم"), max_length=100, blank=True)
    status = models.CharField(
        _("وضعیت ثبت‌نام"), max_length=10, choices=Status.choices,
        default=Status.ENROLLED,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("ثبت‌نام")
        verbose_name_plural = _("ثبت‌نام‌ها")
        unique_together = [("student", "class_ref")]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.student} ← {self.class_ref}"

    def save(self, *args, **kwargs):
        if not self.term:
            self.term = self.class_ref.term
        super().save(*args, **kwargs)
