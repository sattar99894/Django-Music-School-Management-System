"""Forms for the accounts app — student registration & profile."""
from django import forms
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from apps.school.models import Instrument


class RegisterForm(forms.Form):
    """Student self-registration form (multi-instrument selection)."""

    full_name = forms.CharField(
        label="نام و نام خانوادگی",
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "مثال: علی رضایی"}),
    )
    phone = forms.CharField(
        label="شماره موبایل",
        max_length=11,
        widget=forms.TextInput(
            attrs={"placeholder": "09123456789", "inputmode": "numeric", "dir": "ltr"}
        ),
    )
    national_id = forms.CharField(
        label="کد ملی",
        max_length=10,
        widget=forms.TextInput(
            attrs={"placeholder": "۱۰ رقم", "inputmode": "numeric", "dir": "ltr"}
        ),
    )
    instruments = forms.MultipleChoiceField(
        label="ساز(های) مورد علاقه",
        choices=Instrument.choices,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    password = forms.CharField(
        label="رمز عبور",
        min_length=8,
        widget=forms.PasswordInput(attrs={"placeholder": "حداقل ۸ کاراکتر", "dir": "ltr"}),
    )
    password2 = forms.CharField(
        label="تکرار رمز عبور",
        widget=forms.PasswordInput(attrs={"dir": "ltr"}),
    )

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        if not (phone.startswith("09") and len(phone) == 11 and phone.isdigit()):
            raise ValidationError("شماره موبایل باید ۱۱ رقمی و با ۰۹ شروع شود.")
        if User.objects.filter(phone=phone).exists():
            raise ValidationError("این شماره موبایل قبلاً ثبت شده است. وارد شوید.")
        return phone

    def clean_national_id(self):
        nid = self.cleaned_data.get("national_id", "").strip()
        if not (nid.isdigit() and len(nid) == 10):
            raise ValidationError("کد ملی باید دقیقاً ۱۰ رقم باشد.")
        if User.objects.filter(national_id=nid).exists():
            raise ValidationError("این کد ملی قبلاً ثبت شده است.")
        return nid

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") != cleaned.get("password2"):
            raise ValidationError("رمز عبور و تکرار آن یکسان نیستند.")
        return cleaned

    def save(self) -> User:
        from apps.accounts.models import InstrumentProfile, SkillLevel

        user = User.objects.create_user(
            phone=self.cleaned_data["phone"],
            full_name=self.cleaned_data["full_name"],
            password=self.cleaned_data["password"],
            national_id=self.cleaned_data["national_id"],
            role=User.Role.STUDENT,
        )
        # Create an InstrumentProfile per selected instrument (first = primary).
        for i, inst in enumerate(self.cleaned_data.get("instruments", [])):
            InstrumentProfile.objects.create(
                user=user,
                instrument=inst,
                skill_level=SkillLevel.BEGINNER,
                is_primary=(i == 0),
            )
        return user


class ProfileForm(forms.ModelForm):
    """Editable basic profile (name, phone, national ID, avatar).
    Instruments and experiences are managed separately via AJAX."""

    class Meta:
        model = User
        fields = ["full_name", "phone", "national_id", "avatar"]
        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder": "نام و نام خانوادگی"}),
            "phone": forms.TextInput(
                attrs={"inputmode": "numeric", "dir": "ltr", "placeholder": "09123456789"}
            ),
            "national_id": forms.TextInput(
                attrs={"inputmode": "numeric", "dir": "ltr", "placeholder": "۱۰ رقم"}
            ),
            "avatar": forms.FileInput(attrs={"accept": "image/*"}),
        }

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        if not (phone.startswith("09") and len(phone) == 11 and phone.isdigit()):
            raise ValidationError("شماره موبایل باید ۱۱ رقمی و با ۰۹ شروع شود.")
        qs = User.objects.filter(phone=phone).exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("این شماره توسط حساب دیگری استفاده می‌شود.")
        return phone

    def clean_national_id(self):
        nid = (self.cleaned_data.get("national_id") or "").strip()
        if not nid:
            return nid
        if not (nid.isdigit() and len(nid) == 10):
            raise ValidationError("کد ملی باید دقیقاً ۱۰ رقم باشد.")
        qs = User.objects.filter(national_id=nid).exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("این کد ملی توسط حساب دیگری استفاده می‌شود.")
        return nid
