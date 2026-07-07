from django.contrib import admin

from apps.tickets.models import Ticket, TicketMessage


class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 1
    readonly_fields = ("sender", "message", "created_at")


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("title", "student", "category", "priority", "status", "created_at")
    list_filter = ("status", "priority", "category")
    search_fields = ("title", "description", "student__full_name", "student__phone")
    inlines = [TicketMessageInline]
    list_editable = ("status", "priority")


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ("ticket", "sender", "created_at")
    search_fields = ("message",)
