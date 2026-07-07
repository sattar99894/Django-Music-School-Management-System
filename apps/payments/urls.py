from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("request/<int:payment_id>/", views.zarinpal_request, name="zarinpal_request"),
    path("verify/", views.zarinpal_verify, name="zarinpal_verify"),
]
