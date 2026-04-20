from django.db import models

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"

class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    category = models.CharField(max_length=50, choices=[('general', 'General'), ('buying', 'Buying'), ('selling', 'Selling'), ('finance', 'Finance'), ('technical', 'Technical')], default='general')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return self.question

class PrivacyPolicy(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class TermsAndConditions(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class AboutUs(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    mission = models.TextField(blank=True)
    vision = models.TextField(blank=True)
    team_description = models.TextField(blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Sitemap(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class PaymentGatewaySettings(models.Model):
    class Provider(models.TextChoices):
        RAZORPAY = "razorpay", "Razorpay"

    provider = models.CharField(
        max_length=30,
        choices=Provider.choices,
        default=Provider.RAZORPAY,
        unique=True,
    )
    display_name = models.CharField(max_length=100, default="Vehicle Vault Payments")
    key_id = models.CharField(max_length=150, blank=True)
    key_secret = models.CharField(max_length=150, blank=True)
    webhook_secret = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    sandbox_mode = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Payment Gateway Settings"
        verbose_name_plural = "Payment Gateway Settings"

    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.get_provider_display()} ({status})"
