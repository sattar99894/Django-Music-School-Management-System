from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import Experience, InstrumentProfile, User


class InstrumentProfileInline(admin.TabularInline):
    model = InstrumentProfile
    extra = 1
    fields = ("instrument", "skill_level", "started_year", "is_primary")


class ExperienceInline(admin.TabularInline):
    model = Experience
    extra = 1
    fields = ("title", "experience_type", "event_date", "location", "description")


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for the custom User model."""
    list_display = ("phone", "full_name", "role", "national_id", "is_staff", "created_at")
    list_filter = ("role", "is_staff", "is_superuser")
    search_fields = ("phone", "full_name", "national_id", "email")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        ("اطلاعات شخصی", {"fields": ("full_name", "email", "national_id", "avatar")}),
        ("نقش", {"fields": ("role",)}),
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
    inlines = [InstrumentProfileInline, ExperienceInline]
    ordering = ("-created_at",)


@admin.register(InstrumentProfile)
class InstrumentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "instrument", "skill_level", "is_primary", "started_year")
    list_filter = ("instrument", "skill_level", "is_primary")
    search_fields = ("user__full_name", "user__phone")
    list_editable = ("is_primary",)


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "experience_type", "event_date", "location")
    list_filter = ("experience_type",)
    search_fields = ("title", "description", "user__full_name")
