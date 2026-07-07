"""Root URL configuration for the Music School project."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),

    # Public website (landing, courses, course detail, invoice)
    path("", include("apps.core.urls")),

    # Authentication (login, register, logout, admin login)
    path("auth/", include("apps.accounts.urls")),

    # Admin panel (dashboard, classes, directory)
    path("manage/", include("apps.admin_panel.urls")),

    # Payments (Zarinpal request / verify)
    path("payments/", include("apps.payments.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
