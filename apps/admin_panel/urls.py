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
]
