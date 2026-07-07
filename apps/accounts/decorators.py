"""Role-based access decorators."""
from django.contrib.auth.decorators import user_passes_test


def student_required(view):
    """Allow only authenticated students (or teachers)."""
    return user_passes_test(
        lambda u: u.is_authenticated and u.role in (u.Role.STUDENT, u.Role.TEACHER),
        login_url="auth:login",
    )(view)


def admin_required(view):
    """Allow only authenticated admins."""
    return user_passes_test(
        lambda u: u.is_authenticated and u.role == u.Role.ADMIN,
        login_url="auth:admin_login",
    )(view)
