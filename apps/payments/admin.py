from django.contrib import admin

from apps.payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "course", "amount", "status", "ref_id", "created_at")
    list_filter = ("status",)
    search_fields = (
        "student__full_name", "student__phone", "authority", "ref_id",
        "student_name", "student_phone",
    )
    readonly_fields = ("authority", "ref_id", "created_at", "updated_at")
    list_editable = ("status",)
