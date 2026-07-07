from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for the custom User model."""
    list_display = ("phone", "full_name", "role", "national_id", "is_staff", "created_at")
    list_filter = ("role", "is_staff", "is_superuser", "skill_level")
    search_fields = ("phone", "full_name", "national_id", "email")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        ("اطلاعات شخصی", {"fields": ("full_name", "email", "national_id", "avatar")}),
        ("اطلاعات هنرجو", {"fields": ("role", "instrument", "skill_level")}),
        ("دسترسی‌ها", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("تاریخ‌ها", {"fields": ("last_login", "date_joined", "created_at")}),
    )
    readonly_fields = ("last_login", "date_joined", "created_at")
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("phone", "full_name", "password1", "password2", "role"),
        }),
    )
    ordering = ("-created_at",)