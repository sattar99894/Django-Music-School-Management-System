from django.urls import path

from . import views

app_name = "auth"

urlpatterns = [
    # Student auth
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),

    # Admin auth
    path("admin/login/", views.admin_login_view, name="admin_login"),

    # Student panel
    path("dashboard/", views.dashboard, name="dashboard"),
    path("tickets/", views.tickets, name="tickets"),
    path("tickets/create/", views.ticket_create, name="ticket_create"),
    path("tickets/<int:pk>/", views.ticket_detail, name="ticket_detail"),
    path("tickets/<int:pk>/reply/", views.ticket_reply, name="ticket_reply"),
    path("profile/", views.profile, name="profile"),
]
