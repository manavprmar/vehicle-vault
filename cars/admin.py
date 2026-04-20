from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import (
    ActivityLog,
    User,
    Buyer,
    Seller,
    CarCategory,
    Brand,
    DiscoveryPill,
    Car,
    CarListing,
    CarListingImage,
    Purchase,
    TestDrive,
)


# =========================
# USER ADMIN
# =========================
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User

    list_display = ("email", "name", "role", "is_staff", "is_active")
    list_display_links = ("email", "name")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("email", "name", "phone")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("name", "phone", "city", "profile_image")}),
        ("Permissions", {"fields": ("role", "is_staff", "is_active", "is_superuser")}),
        ("Important Dates", {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "name",
                "phone",
                "role",
                "password1",
                "password2",
                "is_staff",
                "is_active",
            ),
        }),
    )

    readonly_fields = ("last_login",)


# =========================
# BUYER ADMIN
# =========================
@admin.register(Buyer)
class BuyerAdmin(admin.ModelAdmin):
    list_display = ("user", "favorite_count")
    search_fields = ("user__email",)
    autocomplete_fields = ("user",)


# =========================
# SELLER ADMIN
# =========================
@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ("user", "dealership_name", "rating")
    search_fields = ("user__email", "dealership_name")
    list_filter = ("rating",)
    autocomplete_fields = ("user",)

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "is_featured", "order", "preview")
    list_editable = ("is_featured", "order")
    search_fields = ("name",)

    @admin.display(description="Logo")
    def preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" width="40" style="border-radius:4px;" />',
                obj.logo.url,
            )
        return "-"

@admin.register(DiscoveryPill)
class DiscoveryPillAdmin(admin.ModelAdmin):
    list_display = ("label", "pill_type", "order")
    list_filter = ("pill_type",)
    list_editable = ("order",)
    search_fields = ("label",)

# =========================
# CAR ADMIN
# =========================
@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = (
        "brand",
        "model",
        "vin",
        "price",
        "stock",
        "is_available",
        "launch_year",
        "preview_image",
    )
    search_fields = ("brand", "model", "vin")
    list_filter = ("launch_year", "is_available", "category")
    readonly_fields = ("slug", "created_at")
    ordering = ("-created_at",)

    @admin.display(description="Image")
    def preview_image(self, obj):
        if obj.car_image:
            return format_html(
                '<img src="{}" width="60" style="border-radius:6px;" />',
                obj.car_image.url,
            )
        return "-"


# =========================
# CAR LISTING IMAGE INLINE
# =========================
class CarListingImageInline(admin.TabularInline):
    model = CarListingImage
    extra = 1


# =========================
# CAR LISTING ADMIN
# =========================
@admin.register(CarListing)
class CarListingAdmin(admin.ModelAdmin):
    list_display = (
        "listing_id",
        "car",
        "seller",
        "price",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "car__brand",
        "car__model",
        "seller__email",
    )
    readonly_fields = ("listing_id", "created_at")
    date_hierarchy = "created_at"
    inlines = (CarListingImageInline,)
    autocomplete_fields = ("car", "seller")
    ordering = ("-created_at",)


# =========================
# CAR LISTING IMAGE ADMIN
# =========================
@admin.register(CarListingImage)
class CarListingImageAdmin(admin.ModelAdmin):
    list_display = ("listing", "alt", "preview")
    autocomplete_fields = ("listing",)

    @admin.display(description="Preview")
    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="60" style="border-radius:6px;" />',
                obj.image.url,
            )
        return "-"


# =========================
# TEST DRIVE ADMIN
# =========================
@admin.register(TestDrive)
class TestDriveAdmin(admin.ModelAdmin):
    list_display = (
        "test_drive_id",
        "listing",
        "buyer",
        "status",
        "proposed_date",
        "created_at",
    )
    list_filter = ("status", "proposed_date")
    search_fields = ("buyer__email",)
    readonly_fields = ("test_drive_id", "created_at")
    autocomplete_fields = ("listing", "buyer")
    ordering = ("-created_at",)


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = (
        "purchase_id",
        "user",
        "car",
        "payment_method",
        "payment_status",
        "is_token_booking",
        "created_at",
    )
    list_filter = ("payment_method", "payment_status", "is_token_booking", "created_at")
    search_fields = (
        "user__email",
        "car__brand",
        "car__model",
        "razorpay_order_id",
        "razorpay_payment_id",
    )
    readonly_fields = (
        "purchase_id",
        "created_at",
        "razorpay_order_id",
        "razorpay_payment_id",
        "razorpay_signature",
    )
    autocomplete_fields = ("user", "car")
    ordering = ("-created_at",)


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action_type", "timestamp")
    list_filter = ("action_type", "timestamp")
    search_fields = ("user__email", "action_type", "description")
    readonly_fields = ("log_id", "timestamp")
    ordering = ("-timestamp",)
