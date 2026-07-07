from django.contrib import admin

from apps.school.models import Class, Course, Enrollment, Teacher


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 1
    fields = ("student", "term", "status", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("user", "specialty", "experience_years", "created_at")
    search_fields = ("user__full_name", "user__phone", "specialty")
    list_filter = ("experience_years",)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "instrument", "level", "price", "teacher", "is_active")
    list_filter = ("instrument", "level", "is_active")
    search_fields = ("title", "slug", "description")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("is_active", "price")


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ("course", "teacher", "term", "capacity", "status", "created_at")
    list_filter = ("status", "term")
    search_fields = ("course__title", "teacher__user__full_name")
    inlines = [EnrollmentInline]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "class_ref", "term", "status", "created_at")
    list_filter = ("status", "term")
    search_fields = ("student__full_name", "student__phone", "class_ref__course__title")
