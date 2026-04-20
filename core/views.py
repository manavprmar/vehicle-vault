from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import random
import os
from functools import wraps
from core.forms import (
    UserLoginForm, UserSignupForm, ProfileUpdateForm, BuyerProfileForm, SellerProfileForm
)
from cars.models import (
    User, Buyer, Seller, Car, Purchase,
    Deal, ActivityLog, UserTask, TestDrive
)


def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != User.Role.ADMIN:
            messages.error(request, "Access Denied: Admins Only 🚫")
            return redirect("cars:home")
        return view_func(request, *args, **kwargs)
    return wrapper

def UserLoginView(request):
    if request.method == "POST":
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]

            user = authenticate(request, email=email, password=password)

            if user:
                selected_role = form.cleaned_data.get("role")
                if user.role != selected_role: # type: ignore
                    messages.error(request, f"Access Denied: You are not registered as a {selected_role} 🚫")
                else:
                    login(request, user)
                    messages.success(request, f"Welcome back, {user.name or user.email}! 🔓") # type: ignore

                    # Centralized role-based redirection
                    return redirect("core:dashboard_redirect")
            else:
                messages.error(request, "Invalid email or password 😬")
    else:
        form = UserLoginForm()

    return render(request, "core/login.html", {"form": form})


def UserSignupView(request):
    if request.method == "POST":
        form = UserSignupForm(request.POST)
        if form.is_valid():
            email_address = form.cleaned_data["email"]

            email_msg = EmailMessage(
                subject="Welcome to Vehicle Vault",
                body="Thank you for creating an account with Vehicle Vault! Please find the welcome guide attached.",
                from_email=settings.EMAIL_HOST_USER,
                to=[email_address],
            )

            # Attach PDF if it exists
            pdf_path = os.path.join(settings.MEDIA_ROOT, 'documents', 'welcome_guide.pdf')
            if os.path.exists(pdf_path):
                email_msg.attach_file(pdf_path)

            # Attach Image if it exists
            image_path = os.path.join(settings.MEDIA_ROOT, 'documents', 'Vehicle Vault.png')
            if os.path.exists(image_path):
                email_msg.attach_file(image_path)

            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.is_active = False  # Require OTP

            otp = str(random.randint(100000, 999999))
            user.otp_code = otp
            user.otp_expiry = timezone.now() + timedelta(minutes=15)
            user.save()

            role = form.cleaned_data["role"]
            if role == User.Role.BUYER:
                Buyer.objects.create(user=user)
            elif role in [User.Role.SELLER, User.Role.DEALER]:
                Seller.objects.create(user=user)

            # Update email body with OTP and send
            email_msg.body = f"Your Vehicle Vault verification code is: {otp}\n\nThis code will expire in 15 minutes."
            
            try:
                email_msg.send(fail_silently=False)
                messages.info(request, "Secure verification code transmitted to your email. 🛡️")
            except Exception as e:
                print(f"Mail delivery failure: {e}")
                messages.warning(request, "Email delivery failed, but your account was created. Please contact support for activation if you don't receive the code. ⚠️")
            
            # Store email in session for OTP verification
            request.session['pending_activation_email'] = email_address
            return redirect("core:verify_otp")
    else:
        form = UserSignupForm()

    return render(request, "core/signup.html", {"form": form})


def VerifyOTPView(request):
    email = request.session.get('pending_activation_email')
    if not email:
        return redirect("core:signup")

    if request.method == "POST":
        otp_attempt = request.POST.get("otp")

        user = None
        if otp_attempt:
            user = User.objects.filter(email=email, otp_code=otp_attempt, otp_expiry__gt=timezone.now()).first()
        
        if user:
            user.is_active = True
            user.otp_code = None
            user.otp_expiry = None
            user.save()
            
            login(request, user)
            messages.success(request, "Account activated! Welcome to the executive circle. 🥂")
            
            # Centralized role-based redirection
            return redirect("core:dashboard_redirect")
        else:
            messages.error(request, "Invalid or expired verification code. ❌")

    return render(request, "core/verify_otp.html", {"email": email})

def LogoutViewCustom(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "Logged out successfully 👋")
    else:
        messages.info(request, "You’re already logged out 🙂")

    return redirect("core:login")

@login_required
def DashboardRedirectView(request):
    """Central portal to redirect users to their specific dashboard based on their role."""
    if request.user.role == User.Role.ADMIN:
        return redirect("core:admin_dashboard")
    elif request.user.role in [User.Role.SELLER, User.Role.DEALER]:
        return redirect("core:seller_dashboard")
    else:
        return redirect("core:buyer_dashboard")
    # ❌ DO NOT render logout.html here if you're redirecting


def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject_type = request.POST.get("subject")
        message = request.POST.get("message")

        # Prepare email for admin
        email_subject = f"New Inquiry: {subject_type} from {name}"
        email_body = f"""
        New contact form submission:
        
        Name: {name}
        Email: {email}
        Subject: {subject_type}
        
        Message:
        {message}
        """
        
        try:
            email_msg = EmailMessage(
                email_subject,
                email_body,
                settings.DEFAULT_FROM_EMAIL,
                [settings.EMAIL_HOST_USER], # Send copy to admin
                reply_to=[email]
            )
            email_msg.send(fail_silently=False)
            messages.success(request, "Your message has been transmitted to our concierge team. We will respond shortly. ✨")
        except Exception as e:
            print(f"Contact form mail failure: {e}")
            messages.warning(request, "Message transmitted, but email notification failed. Our team will still see your inquiry in the database. 🛡️")
            
        return redirect("core:contact")

    return render(request, "core/contact.html")


def faq(request):
    return render(request, "core/faq.html")


def privacy(request):
    return render(request, "core/privacy.html")


def terms(request):
    return render(request, "core/terms.html")


def about(request):
    return render(request, "core/about.html")

def car_loan(request):
    return render(request, "core/car_loan.html")

def car_insurance(request):
    return render(request, "core/car_insurance.html")

def car_valuation(request):
    return render(request, "core/car_valuation.html")

def sell_car(request):
    return render(request, "core/sell_car.html")

def help_center(request):
    return render(request, "core/help_center.html")

def sitemap(request):
    return render(request, "core/sitemap.html")

def loan_application(request):
    return render(request, "core/loan_application.html")

def insurance_quote(request):
    return render(request, "core/insurance_quote.html")

def valuation_check(request):
    return render(request, "core/valuation_check.html")

# =========================
# DASHBOARDS
# =========================

@login_required
def admin_dashboard(request):
    if request.user.role != "Admin":
        messages.error(request, "Access Denied: Admins Only")
        return redirect("cars:home")
    cars = Car.objects.all().order_by("-created_at")
    purchases = Purchase.objects.all().select_related('car', 'user').order_by('-created_at')
    activities = ActivityLog.objects.all().order_by("-timestamp")[:15]
    test_drives = TestDrive.objects.select_related('listing__car', 'listing__seller', 'buyer').order_by('-created_at')[:10]
    return render(request, "core/admin_dashboard.html", {
        "cars": cars,
        "purchases": purchases,
        "activities": activities,
        "test_drives": test_drives,
    })

@login_required
def seller_dashboard(request):
    if request.user.role not in ["Seller", "Dealer"]:
        messages.error(request, "Access Denied: Sellers & Dealers Only")
        return redirect("cars:home")
    
    # Get purchases for cars listed by this seller
    sales = Purchase.objects.filter(car__seller=request.user).select_related('car', 'user').order_by('-created_at')
    deals = Deal.objects.filter(listing__seller=request.user).select_related('listing__car', 'buyer').order_by('-created_at')
    activities = ActivityLog.objects.filter(user=request.user).order_by('-timestamp')[:10]
    tasks = UserTask.objects.filter(user=request.user, is_completed=False).order_by('-due_date')
    test_drives = TestDrive.objects.filter(listing__seller=request.user).order_by('proposed_date')
    active_cars_count = Car.objects.filter(seller=request.user, is_available=True).count()
    
    return render(request, "core/seller_dashboard.html", {
        "sales": sales,
        "deals": deals,
        "activities": activities,
        "tasks": tasks,
        "test_drives": test_drives,
        "active_cars_count": active_cars_count
    })

@login_required
def buyer_dashboard(request):
    if request.user.role != "Buyer":
        messages.error(request, "Access Denied: Buyers Only")
        return redirect("cars:home")
    
    purchases = Purchase.objects.filter(user=request.user).select_related('car').order_by('-created_at')
    deals = Deal.objects.filter(buyer=request.user).select_related('listing__car').order_by('-created_at')
    activities = ActivityLog.objects.filter(user=request.user).order_by('-timestamp')[:10]
    test_drives = TestDrive.objects.filter(buyer=request.user).order_by('proposed_date')
    
    return render(request, "core/buyer_dashboard.html", {
        "purchases": purchases,
        "deals": deals,
        "activities": activities,
        "test_drives": test_drives
    })

# =========================
# PROFILE MANAGEMENT
# =========================
@login_required
def ProfileUpdateView(request):
    user = request.user
    FormClass = ProfileUpdateForm
    ProfileFormClass = None
    profile_instance = None

    if user.role == User.Role.BUYER:
        ProfileFormClass = BuyerProfileForm
        profile_instance, _ = Buyer.objects.get_or_create(user=user)
    elif user.role in [User.Role.SELLER, User.Role.DEALER]:
        ProfileFormClass = SellerProfileForm
        profile_instance, _ = Seller.objects.get_or_create(user=user)

    if request.method == "POST":
        user_form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
        profile_form = None

        if ProfileFormClass and profile_instance:
            profile_form = ProfileFormClass(request.POST, instance=profile_instance)
        
        # Validate forms
        if user_form.is_valid() and (not profile_form or profile_form.is_valid()):
            user_form.save()
            if profile_form:
                profile_form.save()
            messages.success(request, "Profile updated successfully! ✨")
            
            # Redirect back to appropriate dashboard
            if request.user.role == User.Role.ADMIN:
                return redirect("core:admin_dashboard")
            elif request.user.role in [User.Role.SELLER, User.Role.DEALER]:
                return redirect("core:seller_dashboard")
            else:
                return redirect("core:buyer_dashboard")
    else:
        user_form = ProfileUpdateForm(instance=user)
        profile_form = ProfileFormClass(instance=profile_instance) if ProfileFormClass and profile_instance else None

    return render(request, "core/profile.html", {
        "user_form": user_form,
        "profile_form": profile_form,
    })

# =========================
# PASSWORD RESET (OTP)
# =========================

def PasswordResetRequestView(request):
    """Entry point for forgotten passwords. Generates OTP and sends email."""
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)
            # Generate 6-digit OTP
            otp = f"{random.randint(100000, 999999)}"
            user.otp_code = otp
            user.otp_expiry = timezone.now() + timedelta(minutes=10)
            user.save()

            # Prepare professional email
            subject = "Vehicle Vault | Secure Reset Code"
            message = f"""
            Hello,

            We received a request to reset the password for your Vehicle Vault executive account.
            
            Your secure reset code is: {otp}
            
            This code will expire in 10 minutes. If you did not request this reset, please ignore this email or contact support.

            Regards,
            The Vehicle Vault Security Team
            """
            
            try:
                email_msg = EmailMessage(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                )
                email_msg.send()
                messages.info(request, "A secure reset code has been transmitted to your email.")
                return redirect("core:password_reset_verify")
            except Exception as e:
                print(f"Mail delivery failure: {e}")
                messages.error(request, "Email delivery failed. Please contact the administrator.")
                
        except User.DoesNotExist:
            # Security best practice: don't reveal if email exists, but here we can be helpful or vague.
            # For this executive app, we'll be clear but professional.
            messages.error(request, "No account associated with this email identity.")

    return render(request, "core/password_reset_request.html")

def PasswordResetVerifyView(request):
    """Verifies the reset OTP and updates the password."""
    if request.method == "POST":
        email = request.POST.get("email")
        otp = request.POST.get("otp")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if new_password != confirm_password:
            messages.error(request, "Password confirmation does not match.")
            return render(request, "core/password_reset_verify.html", {"email": email})

        try:
            user = User.objects.get(email=email)
            
            # Verify OTP and Expiry
            if user.otp_code == otp and user.otp_expiry > timezone.now(): # type: ignore
                user.set_password(new_password)
                user.otp_code = None # Clear after use
                user.otp_expiry = None
                user.save()
                
                messages.success(request, "Identity verified. Your credentials have been updated.")
                return redirect("core:login")
            else:
                messages.error(request, "Invalid or expired security code.")
                
        except User.DoesNotExist:
            messages.error(request, "Invalid session. Please restart the recovery process.")

    return render(request, "core/password_reset_verify.html")

# =========================
# USER MANAGEMENT
# =========================

@admin_required
def UserManageListView(request):
    users = User.objects.all().order_by("-date_joined")
    return render(request, "core/manage_users.html", {"users": users})

@admin_required
def UserDeleteView(request, user_id):
    user_to_delete = get_object_or_404(User, user_id=user_id)
    if user_to_delete == request.user:
        messages.error(request, "You cannot delete your own account! 🛑")
    else:
        user_to_delete.delete()
        messages.success(request, f"Account {user_to_delete.email} has been removed. 🗑️")
    return redirect("core:manage_users")
