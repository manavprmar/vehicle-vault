from django.contrib import admin

from .models import (
    AboutUs,
    ContactMessage,
    FAQ,
    PaymentGatewaySettings,
    PrivacyPolicy,
    Sitemap,
    TermsAndConditions,
)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "created_at")
    search_fields = ("name", "email", "subject")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "category", "order", "is_active")
    list_filter = ("category", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("question", "answer")


@admin.register(PrivacyPolicy)
class PrivacyPolicyAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "last_updated")
    list_filter = ("is_active",)
    search_fields = ("title", "content")


@admin.register(TermsAndConditions)
class TermsAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "last_updated")
    list_filter = ("is_active",)
    search_fields = ("title", "content")


@admin.register(AboutUs)
class AboutUsAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "last_updated")
    list_filter = ("is_active",)
    search_fields = ("title", "content", "mission", "vision")


@admin.register(Sitemap)
class SitemapAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "last_updated")
    list_filter = ("is_active",)
    search_fields = ("title", "content")


@admin.register(PaymentGatewaySettings)
class PaymentGatewaySettingsAdmin(admin.ModelAdmin):
    list_display = ("provider", "display_name", "is_active", "sandbox_mode", "updated_at")
    list_filter = ("provider", "is_active", "sandbox_mode")
    search_fields = ("provider", "display_name", "key_id")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("provider", "display_name", "is_active", "sandbox_mode")}),
        ("Credentials", {"fields": ("key_id", "key_secret", "webhook_secret")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
