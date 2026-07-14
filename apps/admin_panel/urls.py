from django.urls import path

from . import views

app_name = "admin_panel"

urlpatterns = [
    # Dashboard
    path("", views.dashboard, name="dashboard"),

    # Classes management
    path("classes/", views.classes_list, name="classes"),
    path("classes/<int:pk>/", views.class_detail, name="class_detail"),
    path("classes/<int:pk>/add-student/", views.class_add_student, name="class_add_student"),
    path(
        "classes/<int:pk>/remove/<int:enrollment_id>/",
        views.class_remove_student,
        name="class_remove_student",
    ),

    # Student search (AJAX, for add-to-class modal)
    path("students/search/", views.student_search, name="student_search"),

    # Students & Teachers directory
    path("directory/", views.directory, name="directory"),

    # Student / Teacher detail
    path("users/<int:pk>/", views.student_detail, name="student_detail"),

    # Tickets management
    path("tickets/", views.tickets_list, name="tickets"),
    path("tickets/<int:pk>/", views.ticket_detail, name="ticket_detail"),
    path("tickets/<int:pk>/reply/", views.ticket_reply, name="ticket_reply"),
    path("tickets/<int:pk>/close/", views.ticket_close, name="ticket_close"),

    # Payments management
    path("payments/", views.payments_list, name="payments"),
    path("payments/<int:pk>/", views.payment_detail, name="payment_detail"),
]
