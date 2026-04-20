from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


# =========================
# LOGIN FORM
# =========================
class UserLoginForm(forms.Form):
    name = forms.CharField(
        label="Full Name",
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Your full name",
        })
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "you@example.com",
            "autocomplete": "email",
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "••••••••",
            "autocomplete": "current-password",
        })
    )
    role = forms.ChoiceField(
        choices=User.Role.choices, # type: ignore
        widget=forms.Select(attrs={
            "class": "form-select"
        })
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        required=False,
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Repeat password",
        })
    )


# =========================
# SIGNUP FORM
# =========================
class UserSignupForm(forms.ModelForm):
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Create a strong password",
            "autocomplete": "new-password",
        })
    )

    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Repeat password",
            "autocomplete": "new-password",
        })
    )

    role = forms.ChoiceField(
        choices=User.Role.choices, # type: ignore
        widget=forms.RadioSelect(attrs={
            "class": "form-check-input"
        })
    )

    class Meta:
        model = User
        fields = ["email", "name", "role"]
        widgets = {
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "you@example.com",
            }),
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Your full name",
            }),
            }

    # 🔐 Password match check
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")

        if password and confirm and password != confirm:
            raise ValidationError("Passwords do not match 😬")

        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get("email").lower() # type: ignore
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered 👀")
        return email

# =========================
# PROFILE FORMS
# =========================
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["name", "phone", "city", "profile_image"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "profile_image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

from cars.models import Buyer, Seller

class BuyerProfileForm(forms.ModelForm):
    # For now, preferences can be input as plain text or just hidden if complex,
    # Let's make it a Textarea or CharField if needed, but since it's JSONField:
    # We will exclude it or handle it simply. Let's exclude preferences for now and handle it if needed later, 
    # or expose a specific field. We can omit it if no specific buyer fields are needed right now, 
    # but let's add it for completeness if preferences are strings.
    # Actually, let's keep it simple.
    class Meta:
        model = Buyer
        fields = [] # Add fields if needed later

class SellerProfileForm(forms.ModelForm):
    class Meta:
        model = Seller
        fields = ["dealership_name", "location"]
        widgets = {
            "dealership_name": forms.TextInput(attrs={"class": "form-control"}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
        }