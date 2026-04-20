from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone

from cars.models import (
    User,
    Buyer,
    Seller,
    CarCategory,
    Car,
    CarListing,
    CarListingImage,
    TestDrive,
    Purchase,
)


class UserLoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

class CarCategoryForm(forms.ModelForm):
    class Meta:
        model = CarCategory
        fields = ("name",)
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"})
        }
    def clean_name(self):
        name = self.cleaned_data["name"].lower()
        if CarCategory.objects.filter(name=name).exists():
            raise ValidationError("Category already exists.")
        return name

class CarForm(forms.ModelForm):
    images = forms.FileField(
        widget=forms.TextInput(attrs={'type': 'file', 'multiple': True, 'class': 'form-control'}), 
        required=False, 
        label="High-Res Gallery Images"
    )

    class Meta:
        model = Car
        exclude = (
            "created_at",
            "is_available",
            "slug",
            "seller",
            "horsepower",
            "torque",
            "top_speed",
            "acceleration_0_100",
            "engine_details",
            "safety_rating",
            "three_d_model_url",
        )
        widgets = {
            "category": forms.Select(attrs={"class": "form-select"}),
            "vin": forms.TextInput(attrs={"class": "form-control"}),
            "brand": forms.TextInput(attrs={"class": "form-control"}),
            "model": forms.TextInput(attrs={"class": "form-control"}),
            "fuel_type": forms.Select(attrs={"class": "form-select"}),
            "transmission": forms.Select(attrs={"class": "form-select"}),
            "seating_capacity": forms.NumberInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control"}),
            "mileage": forms.TextInput(attrs={"class": "form-control"}),
            "launch_year": forms.NumberInput(attrs={"class": "form-control"}),
            "stock": forms.NumberInput(attrs={"class": "form-control"}),
            "car_image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "is_upcoming": forms.CheckboxInput(attrs={"class": "form-check-input mt-0"}),
            "is_electric": forms.CheckboxInput(attrs={"class": "form-check-input mt-0"}),
        }

    def clean_vin(self):
        vin = self.cleaned_data["vin"].upper()
        qs = Car.objects.filter(vin=vin)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("VIN already exists.")
        return vin

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price <= 0:
            raise ValidationError("Price must be greater than 0.")
        return price

    def clean_stock(self):
        stock = self.cleaned_data["stock"]
        if stock < 0:
            raise ValidationError("Stock cannot be negative.")
        return stock

    def clean_launch_year(self):
        year = self.cleaned_data["launch_year"]
        current_year = timezone.now().year
        if year < 1950 or year > current_year + 1:
            raise ValidationError("Enter a valid launch year.")
        return year

class CarListingForm(forms.ModelForm):
    class Meta:
        model = CarListing
        fields = ("car", "price", "mileage", "description", "status")
        widgets = {
            "car": forms.Select(attrs={"class": "form-select"}),
            "price": forms.NumberInput(attrs={"class": "form-control"}),
            "mileage": forms.NumberInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price <= 0:
            raise ValidationError("Price must be greater than 0.")
        return price
class CarListingImageForm(forms.ModelForm):
    class Meta:
        model = CarListingImage
        fields = ("image", "alt")
        widgets = {
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "alt": forms.TextInput(attrs={"class": "form-control"}),
        }
    def clean_image(self):
        image = self.cleaned_data["image"]
        if not image:
            raise ValidationError("Image is required.")
        return image
class TestDriveForm(forms.ModelForm):
    class Meta:
        model = TestDrive
        fields = ("listing", "proposed_date", "actual_date", "status", "notes")
        widgets = {
            "listing": forms.Select(attrs={"class": "form-select"}),
            "proposed_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "actual_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def clean_proposed_date(self):
        date = self.cleaned_data["proposed_date"]
        if date < timezone.now().date():
            raise ValidationError("Proposed date cannot be in the past.")
        return date

class BuyerTestDriveForm(forms.ModelForm):
    class Meta:
        model = TestDrive
        fields = ("proposed_date", "notes")
        widgets = {
            "proposed_date": forms.DateInput(attrs={"type": "date", "class": "form-control", "style": "background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.1); color: white;"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 4, "style": "background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.1); color: white;", "placeholder": "Any specific requests or preferred times?"}),
        }

    def clean_proposed_date(self):
        date = self.cleaned_data["proposed_date"]
        if date < timezone.now().date():
            raise ValidationError("Proposed date cannot be in the past.")
        return date

class PurchaseForm(forms.ModelForm):
    # EMI options
    EMI_CHOICES = [
        (3, '3 Months'),
        (6, '6 Months'),
        (12, '12 Months'),
        (24, '24 Months'),
    ]
    emi_months = forms.ChoiceField(
        choices=EMI_CHOICES, 
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    down_payment = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter down payment', 'step': '0.01'})
    )
    
    shipping_address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': '123 Executive Drive...'}),
    )
    
    contact_number = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 XXXX XXXXXX'}),
    )
    
    is_token_booking = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Purchase
        fields = ('payment_method', 'emi_months', 'down_payment', 'shipping_address', 'contact_number', 'is_token_booking')
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-select', 'id': 'id_payment_method'}),
        }


    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        emi_months = cleaned_data.get('emi_months')
        down_payment = cleaned_data.get('down_payment')

        if payment_method == 'EMI':
            if not emi_months:
                self.add_error('emi_months', 'Please select EMI duration.')
            if down_payment is None or down_payment < 0:
                self.add_error('down_payment', 'Enter a valid down payment.')
        
        return cleaned_data
