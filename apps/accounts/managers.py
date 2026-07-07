"""Custom user manager — authenticates with phone number instead of username."""
from django.contrib.auth.base_user import BaseUserManager


class CustomUserManager(BaseUserManager):
    """User manager that uses `phone` as the unique identifier."""

    use_in_migrations = True

    def _create_user(self, phone, full_name, password, **extra_fields):
        if not phone:
            raise ValueError("شماره موبایل الزامی است.")
        user = self.model(phone=phone, full_name=full_name or "", **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone, full_name="", password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", "STUDENT")
        return self._create_user(phone, full_name, password, **extra_fields)

    def create_superuser(self, phone, full_name="", password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "ADMIN")
        if extra_fields.get("is_staff") is not True:
            raise ValueError("کاربر ارشد باید is_staff=True باشد.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("کاربر ارشد باید is_superuser=True باشد.")
        return self._create_user(phone, full_name, password, **extra_fields)
