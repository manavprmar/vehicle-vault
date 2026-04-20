from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from django.utils.text import slugify
import uuid

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        if 'vault_code' not in extra_fields:
            extra_fields['vault_code'] = email
        if 'status' not in extra_fields:
            extra_fields['status'] = "Inactive"

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.update({
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
            "role": User.Role.ADMIN,
        })
        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    vault_code = models.CharField(max_length=150, unique=True, blank=True, null=True)
    username = None # Remove AbstractUser's username
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)

    name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=50, blank=True)
    profile_image = models.ImageField(upload_to="users/", blank=True, null=True)

    class Role(models.TextChoices):
        BUYER = "Buyer", "Buyer"
        SELLER = "Seller", "Seller"
        DEALER = "Dealer", "Dealer"
        ADMIN = "Admin", "Admin"

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.BUYER,
        db_index=True,
    )

    is_active = models.BooleanField(default=False) # Overrides AbstractUser's default True
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_expiry = models.DateTimeField(blank=True, null=True)

    class AccountStatus(models.TextChoices):
        INACTIVE = "Inactive", "Inactive"
        ACTIVE = "Active", "Active"
        BLOCKED = "Blocked", "Blocked"
        DELETED = "Deleted", "Deleted"

    status = models.CharField(
        max_length=10,
        choices=AccountStatus.choices,
        default=AccountStatus.INACTIVE,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager() # type: ignore

    def __str__(self):
        return self.email

class Buyer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="buyer_profile")
    preferences = models.JSONField(blank=True, null=True)
    favorite_count = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        if self.user.role != User.Role.BUYER:
            self.user.role = User.Role.BUYER
            self.user.save(update_fields=["role"])
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Buyer | {self.user.email}"


class Seller(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="seller_profile")
    dealership_name = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=150, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00) # type: ignore

    def save(self, *args, **kwargs):
        if self.user.role not in [User.Role.SELLER, User.Role.DEALER]:
            self.user.role = User.Role.SELLER
            self.user.save(update_fields=["role"])
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Seller | {self.user.email}"

class CarCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to="brands/", blank=True, null=True)
    is_featured = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

class DiscoveryPill(models.Model):
    label = models.CharField(max_length=50)
    filter_value = models.CharField(max_length=100)
    pill_type = models.CharField(
        max_length=20,
        choices=[
            ('Budget', 'Budget'), 
            ('Body Type', 'Body Type'),
            ('Fuel Type', 'Fuel Type'),
            ('Transmission', 'Transmission'),
            ('Seating', 'Seating Capacity'),
            ('Popular', 'Popular Searches')
        ],
        default='Budget'
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['pill_type', 'order']

    def __str__(self):
        return f"{self.pill_type}: {self.label}"

class Car(models.Model):
    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="cars",
        limit_choices_to={"role__in": ["Seller", "Admin"]},
    )

    category = models.ForeignKey(
        CarCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cars",
    )

    vin = models.CharField(max_length=100, unique=True)
    brand = models.CharField(max_length=100, db_index=True)
    model = models.CharField(max_length=100, db_index=True)
    slug = models.SlugField(unique=True, blank=True)

    price = models.DecimalField(max_digits=12, decimal_places=2)
    fuel_type = models.CharField(
        max_length=20,
        choices=[
            ("Petrol", "Petrol"),
            ("Diesel", "Diesel"),
            ("Electric", "Electric"),
            ("Hybrid", "Hybrid"),
        ],
        default="Petrol",
    )
    transmission = models.CharField(
        max_length=20,
        choices=[
            ("Manual", "Manual"),
            ("Automatic", "Automatic"),
        ],
        default="Manual",
    )
    seating_capacity = models.PositiveIntegerField(default=5)
    mileage = models.CharField(max_length=50)
    launch_year = models.PositiveIntegerField()
    stock = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)

    car_image = models.ImageField(upload_to="cars/", blank=True, null=True)
    is_upcoming = models.BooleanField(default=False)
    is_electric = models.BooleanField(default=False)
    
    # Enhanced Technical Specs
    horsepower = models.PositiveIntegerField(default=0)
    torque = models.PositiveIntegerField(default=0)
    top_speed = models.PositiveIntegerField(default=0)
    acceleration_0_100 = models.DecimalField(max_digits=4, decimal_places=1, default=0.0) # type: ignore
    engine_details = models.CharField(max_length=200, blank=True)
    safety_rating = models.CharField(max_length=10, default="N/A")
    three_d_model_url = models.URLField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.is_available = self.stock > 0
        if self.fuel_type in ["Electric", "EV"]:
            self.is_electric = True
        
        if not self.slug:
            self.slug = slugify(f"{self.brand}-{self.model}-{self.launch_year}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.brand} {self.model}"

class CarImage(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="gallery")
    image = models.ImageField(upload_to='car_gallery/')
    is_feature = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Gallery Media: {self.car.brand} {self.car.model}"

class CarListing(models.Model):
    listing_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="listings")
    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="listings",
        limit_choices_to={"role__in": ["Seller", "Admin"]},
    )

    price = models.DecimalField(max_digits=12, decimal_places=2)
    mileage = models.PositiveIntegerField()
    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ("Active", "Active"), 
            ("Pending", "Pending"), 
            ("Sold", "Sold"), 
            ("Withdrawn", "Withdrawn")
        ],
        default="Active",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.car} | {self.status}"

class CarListingImage(models.Model):
    listing = models.ForeignKey(CarListing, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="car_listings/")
    alt = models.CharField(max_length=100, blank=True)

    def save(self, *args, **kwargs):
        if not self.alt:
            self.alt = self.image.name
        super().save(*args, **kwargs)

class TestDrive(models.Model):
    test_drive_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    listing = models.ForeignKey(CarListing, on_delete=models.CASCADE, related_name="test_drives")
    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "Buyer"},
        related_name="test_drives",
    )

    proposed_date = models.DateField()
    actual_date = models.DateField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ("Pending", "Pending"),
            ("Confirmed", "Confirmed"),
            ("Completed", "Completed"),
            ("Cancelled", "Cancelled"),
        ],
        default="Pending",
    )


    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Purchase(models.Model):
    purchase_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="purchases")
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="purchases")
    
    price = models.DecimalField(max_digits=12, decimal_places=2)
    
    PAYMENT_METHOD_CHOICES = [
        ("Cash", "Cash"),
        ("Card", "Card"),
        ("Bank Transfer", "Bank Transfer"),
        ("EMI", "EMI"),
    ]
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default="Cash")
    
    PAYMENT_STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
    ]
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="Pending")
    
    # EMI Details
    is_emi = models.BooleanField(default=False)
    emi_months = models.PositiveIntegerField(null=True, blank=True)
    monthly_installment = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    down_payment = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # Razorpay Gateway Tracking
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=200, blank=True, null=True)
    
    # Logistics & Token Bookings
    is_token_booking = models.BooleanField(default=False)
    shipping_address = models.TextField(blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Purchase {self.purchase_id} | {self.car} | {self.user.email}"

class Message(models.Model):
    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    listing = models.ForeignKey(CarListing, on_delete=models.CASCADE, related_name="messages", null=True, blank=True)
    
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"From {self.sender} to {self.recipient}"

class Deal(models.Model):
    deal_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.ForeignKey(CarListing, on_delete=models.CASCADE, related_name="deals")
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="deals_as_buyer")
    
    offered_price = models.DecimalField(max_digits=12, decimal_places=2)
    message = models.TextField(blank=True)
    
    class Status(models.TextChoices):
        PROPOSED = "Proposed", "Proposed"
        NEGOTIATING = "Negotiating", "Negotiating"
        ACCEPTED = "Accepted", "Accepted"
        REJECTED = "Rejected", "Rejected"
        CANCELLED = "Cancelled", "Cancelled"

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROPOSED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Deal on {self.listing.car} | {self.status}"

class ActivityLog(models.Model):
    log_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activities")
    action_type = models.CharField(max_length=50) # e.g., 'Listing Created', 'Price Updated', 'Message Sent'
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.email} - {self.action_type} at {self.timestamp}"

class UserTask(models.Model):
    task_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['due_date', 'created_at']

    def __str__(self):
        return self.title

class Wishlist(models.Model):
    wishlist_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="wishlist_items"
    )
    car = models.ForeignKey(
        Car, on_delete=models.CASCADE, related_name="wishlisted_by"
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "car")
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.user.email} â†’ {self.car}"
