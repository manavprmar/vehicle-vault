from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PaymentGatewaySettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("provider", models.CharField(choices=[("razorpay", "Razorpay")], default="razorpay", max_length=30, unique=True)),
                ("display_name", models.CharField(default="Vehicle Vault Payments", max_length=100)),
                ("key_id", models.CharField(blank=True, max_length=150)),
                ("key_secret", models.CharField(blank=True, max_length=150)),
                ("webhook_secret", models.CharField(blank=True, max_length=150)),
                ("is_active", models.BooleanField(default=True)),
                ("sandbox_mode", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Payment Gateway Settings",
                "verbose_name_plural": "Payment Gateway Settings",
            },
        ),
    ]
