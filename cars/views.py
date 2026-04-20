from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from functools import wraps

from cars.forms import (
    CarListingForm,
    CarForm,
    CarListingImageForm,
    TestDriveForm,
    BuyerTestDriveForm,
    PurchaseForm,
)
from cars.models import (
    Car,
    CarCategory,
    Brand,
    DiscoveryPill,
    CarListing,
    TestDrive,
    CarImage,
    Purchase,
    Message,
    Deal,
    ActivityLog,
    UserTask,
    Wishlist,
)
from cars.utils import (
    ensure_primary_listing,
    get_payment_gateway_credentials,
    get_static_brand_showcase,
    get_static_gallery_images,
    get_static_hero_images,
    log_activity,
    payment_gateway_is_configured,
    sync_static_inventory,
)
import razorpay
import uuid


User = get_user_model()


def get_amount_paid_now(purchase):
    if purchase.is_token_booking:
        return 50000.0
    if purchase.is_emi and purchase.down_payment:
        return float(purchase.down_payment)
    return float(purchase.price)


def build_purchase_timeline(purchase):
    listing = purchase.car.listings.order_by("-created_at").first() # type: ignore
    buyer_logs = ActivityLog.objects.filter(user=purchase.user).order_by("timestamp")
    seller_logs = (
        ActivityLog.objects.filter(user=listing.seller).order_by("timestamp")
        if listing is not None
        else ActivityLog.objects.none()
    )

    def first_log(logs, action_type):
        return logs.filter(action_type=action_type).first()

    payment_initiated_log = first_log(buyer_logs, "Payment Initiated")
    payment_verified_log = first_log(buyer_logs, "Payment Verified")
    receipt_generated_log = first_log(buyer_logs, "Receipt Generated")
    asset_sold_log = first_log(seller_logs, "Asset Sold")

    seller_confirmed_at = None
    if listing is not None and listing.status in ["Pending", "Sold"]:
        seller_confirmed_at = asset_sold_log.timestamp if asset_sold_log else listing.created_at

    delivery_pending_at = None
    if purchase.payment_status == "Completed":
        delivery_pending_at = asset_sold_log.timestamp if asset_sold_log else purchase.created_at

    timeline = [
        {
            "title": "Request Created",
            "description": "Purchase request was created for this vehicle.",
            "completed": True,
            "current": False,
            "timestamp": purchase.created_at,
        },
        {
            "title": "Seller Confirmed",
            "description": "Seller approved the order and moved the vehicle toward fulfillment.",
            "completed": seller_confirmed_at is not None,
            "current": seller_confirmed_at is None and purchase.payment_status == "Pending",
            "timestamp": seller_confirmed_at,
        },
        {
            "title": "Payment Initiated",
            "description": "Secure gateway order was created and payment was initiated.",
            "completed": bool(purchase.razorpay_order_id),
            "current": bool(purchase.razorpay_order_id) and purchase.payment_status == "Pending",
            "timestamp": payment_initiated_log.timestamp if payment_initiated_log else purchase.created_at if purchase.razorpay_order_id else None,
        },
        {
            "title": "Payment Verified",
            "description": "Gateway signature was verified successfully.",
            "completed": purchase.payment_status == "Completed",
            "current": False,
            "timestamp": payment_verified_log.timestamp if payment_verified_log else purchase.created_at if purchase.payment_status == "Completed" else None,
        },
        {
            "title": "Receipt Generated",
            "description": "Digital purchase receipt is ready for print or download.",
            "completed": purchase.payment_status == "Completed",
            "current": False,
            "timestamp": receipt_generated_log.timestamp if receipt_generated_log else purchase.created_at if purchase.payment_status == "Completed" else None,
        },
        {
            "title": "Car Marked Sold / Delivery Pending",
            "description": "Inventory is updated and the order is awaiting delivery coordination.",
            "completed": delivery_pending_at is not None,
            "current": purchase.payment_status == "Completed" and delivery_pending_at is not None,
            "timestamp": delivery_pending_at,
        },
    ]
    return timeline


def ensure_inventory_categories():
    for category_name in ("Sedan", "SUV", "Hatchback"):
        CarCategory.objects.get_or_create(name=category_name)

def seller_or_admin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in [User.Role.SELLER, User.Role.ADMIN]: # type: ignore
            messages.error(request, "Seller or Admin access only.")
            return redirect("cars:home")
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != User.Role.ADMIN:  # type: ignore
            messages.error(request, "Admin access only.")
            return redirect("cars:inventory")
        return view_func(request, *args, **kwargs)
    return wrapper


def buyer_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != User.Role.BUYER:  # type: ignore
            messages.error(request, "Only buyers can request test drives.")
            return redirect("cars:home")
        return view_func(request, *args, **kwargs)
    return wrapper

def HomeView(request):
    listings = (
        CarListing.objects
        .select_related("car", "seller")
        .prefetch_related("images")
        .order_by("-created_at")[:8]
    )
    brands = Brand.objects.all().order_by('order', 'name')
    return render(request, "home.html", {
        "listings": listings,
        "brand_showcase": get_static_brand_showcase(brands),
        "hero_images": get_static_hero_images(),
    })

def find_new(request):
    brands = Brand.objects.all().order_by("order", "name")
    return render(request, "cars/find_new.html", {
        "brand_showcase": get_static_brand_showcase(brands),
    })

def CarsListView(request):
    cars = Car.objects.order_by("-created_at")

    fuel = request.GET.get("fuel")
    budget = request.GET.get("budget")
    q = request.GET.get("q")
    brand = request.GET.get("brand")
    body_type = request.GET.get("body_type") or request.GET.get("filter")
    transmission = request.GET.get("transmission")
    seating = request.GET.get("seating")

    if fuel:
        cars = cars.filter(fuel_type__iexact=fuel)
    if q:
        cars = cars.filter(Q(brand__icontains=q) | Q(model__icontains=q))
    if brand:
        cars = cars.filter(brand__icontains=brand)
    if body_type:
        cars = cars.filter(category__name__icontains=body_type)
    if transmission:
        cars = cars.filter(transmission__iexact=transmission)
    if seating:
        cars = cars.filter(seating_capacity=seating)
    if budget:
        try:
            budget_lower = budget.lower()
            if "under" in budget_lower:
                parts = [p for p in budget_lower.split("-") if p.isdigit()]
                if parts:
                    max_val = int(parts[0]) * 100000
                    cars = cars.filter(price__lt=max_val)
            elif "over" in budget_lower:
                parts = [p for p in budget_lower.split("-") if p.isdigit()]
                if parts:
                    min_val = int(parts[0]) * 100000
                    cars = cars.filter(price__gt=min_val)
            elif "-" in budget:
                parts = [p for p in budget.split("-") if p.isdigit()]
                if len(parts) >= 2:
                    min_val = int(parts[0]) * 100000
                    max_val = int(parts[1]) * 100000
                    cars = cars.filter(price__range=(min_val, max_val))
        except (ValueError, IndexError):
            pass 

    pills = DiscoveryPill.objects.all()
    
    discovery_context = {
        "budget_pills": pills.filter(pill_type="Budget"),
        "body_pills": pills.filter(pill_type="Body Type"),
        "fuel_pills": pills.filter(pill_type="Fuel Type"),
        "transmission_pills": pills.filter(pill_type="Transmission"),
        "seating_pills": pills.filter(pill_type="Seating"),
        "popular_pills": pills.filter(pill_type="Popular"),
    }

    brands = Brand.objects.all().order_by("order", "name")
    static_car_images = get_static_gallery_images()

    wishlisted_ids = []
    if request.user.is_authenticated:
        wishlisted_ids = Wishlist.objects.filter(user=request.user).values_list("car_id", flat=True)

    context = {
        "cars": cars.distinct(),
        "brand_showcase": get_static_brand_showcase(brands),
        "static_car_images": static_car_images,
        "wishlisted_ids": list(wishlisted_ids),
        **discovery_context,
    }

    return render(request, "cars/all_cars.html", context)

def UsedCarsListView(request):
    cars = Car.objects.filter(stock__gt=0).order_by("-created_at")
    return render(request, "cars/used_cars.html", {"cars": cars})

@seller_or_admin_required
def InventoryListView(request):
    if request.user.role == User.Role.ADMIN: # type: ignore
        cars = Car.objects.select_related("seller", "category").all().order_by("-created_at")
    else:
        cars = Car.objects.select_related("seller", "category").filter(seller=request.user).order_by("-created_at")
    
    return render(request, "cars/inventory.html", {"cars": cars})

def UpcomingCarsListView(request):
    cars = Car.objects.filter(launch_year__gte=2026).order_by("launch_year")
    return render(request, "cars/upcoming_cars.html", {"cars": cars})

def ElectricCarsListView(request):
    cars = Car.objects.filter(
        Q(fuel_type__iexact="Electric") | 
        Q(fuel_type__iexact="EV")
    ).order_by("-created_at")
    return render(request, "cars/electric_cars.html", {"cars": cars})

def NewCarsListView(request):
    cars = Car.objects.filter(launch_year=2025).order_by("-created_at")
    return render(request, "cars/new_cars.html", {"cars": cars})

def CarDetailView(request, vin):
    car = get_object_or_404(Car, vin=vin)
    
    brand = Brand.objects.filter(name__iexact=car.brand).first()
    similar_cars = Car.objects.filter(
        Q(category=car.category) | Q(brand=car.brand)
    ).exclude(vin=car.vin)[:4]
    
    is_wishlisted = False
    if request.user.is_authenticated:
        is_wishlisted = Wishlist.objects.filter(user=request.user, car=car).exists()

    context = {
        "car": car,
        "brand": brand,
        "similar_cars": similar_cars,
        "is_wishlisted": is_wishlisted
    }
    return render(request, "cars/car_detail.html", context)

def CarCategoryView(request, category_name):
    category = get_object_or_404(CarCategory, name__iexact=category_name)
    cars = Car.objects.filter(category=category).order_by("-created_at").select_related("seller")
    
    context = {
        "category": category,
        "cars": cars,
        "category_name": category_name
    }
    return render(request, "cars/car_category.html", context)

@seller_or_admin_required
def CarCreateView(request):
    ensure_inventory_categories()
    form = CarForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        car = form.save(commit=False)
        car.seller = request.user
        
        images = request.FILES.getlist("images")
        if images and not car.car_image:
            car.car_image = images[0]
            
        car.save()
        ensure_primary_listing(
            car,
            description=f"{car.brand} {car.model} listed by {request.user.name or request.user.email}.",
        )
        
        # Populate the Multi-Image Media Gallery
        if images:
            for img in images:
                CarImage.objects.create(car=car, image=img)

        log_activity(request.user, "Listing Created", f"New asset '{car.brand} {car.model}' (VIN: {car.vin}) registered in inventory.")
        messages.success(request, "Asset registered successfully with multi-media gallery ðŸ“¸")
        return redirect("cars:inventory")

    if request.method == "POST":
        messages.error(request, "Listing could not be deployed. Please correct the highlighted fields and try again.")

    return render(request, "cars/add_car.html", {
        "car_form": form,
    })

@seller_or_admin_required
def CarUpdateView(request, vin):
    ensure_inventory_categories()
    if request.user.role == User.Role.ADMIN: # type: ignore
        car = get_object_or_404(Car, vin=vin)
    else:
        car = get_object_or_404(Car, vin=vin, seller=request.user)

    form = CarForm(request.POST or None, request.FILES or None, instance=car)

    if request.method == "POST" and form.is_valid():
        car = form.save(commit=False)
        
        images = request.FILES.getlist("images")
        if images and not car.car_image:
            car.car_image = images[0]
            
        car.save()
        ensure_primary_listing(
            car,
            description=f"{car.brand} {car.model} listed by {car.seller.name or car.seller.email}.",
        )
        
        # Append additional media to the existing gallery
        if images:
            for img in images:
                CarImage.objects.create(car=car, image=img)

        log_activity(request.user, "Listing Updated", f"Asset '{car.brand} {car.model}' (VIN: {car.vin}) specifications revised.")
        messages.success(request, "Asset updated successfully âœ¨")
        return redirect("cars:inventory")

    if request.method == "POST":
        messages.error(request, "Listing update could not be saved. Please correct the highlighted fields and try again.")

    return render(request, "cars/add_car.html", {
        "car_form": form,
        "car": car
    })

@seller_or_admin_required
def CarDeleteView(request, vin):
    if request.user.role == User.Role.ADMIN: # type: ignore
        car = get_object_or_404(Car, vin=vin)
    else:
        car = get_object_or_404(Car, vin=vin, seller=request.user)
    log_activity(request.user, "Listing Deleted", f"Asset '{car.brand} {car.model}' (VIN: {car.vin}) permanently removed.")
    car.delete()
    messages.success(request, "Car deleted successfully ðŸ—‘ï¸")
    return redirect("cars:inventory")

@seller_or_admin_required
def QuickPriceUpdateView(request, vin):
    """Allow seller/admin to instantly update car price without going through full edit form."""
    if request.user.role == User.Role.ADMIN: # type: ignore
        car = get_object_or_404(Car, vin=vin)
    else:
        car = get_object_or_404(Car, vin=vin, seller=request.user)

    if request.method == "POST":
        try:
            new_price = float(request.POST.get("price", 0))
            if new_price <= 0:
                raise ValueError("Price must be > 0")
            old_price = car.price
            car.price = new_price
            car.save()
            ensure_primary_listing(car)
            log_activity(
                request.user,
                "Price Updated",
                f"Price of '{car.brand} {car.model}' (VIN: {car.vin}) updated from â‚¹{old_price} â†’ â‚¹{new_price}."
            )
            messages.success(request, f"Price updated to â‚¹{new_price:,.0f} successfully âœ…")
        except (ValueError, TypeError):
            messages.error(request, "Invalid price entered. Please enter a valid number greater than 0. âŒ")

    return redirect("cars:inventory")

@seller_or_admin_required
def QuickStockUpdateView(request, vin):
    """Allow seller/admin to instantly update car stock count from inventory."""
    if request.user.role == User.Role.ADMIN: # type: ignore
        car = get_object_or_404(Car, vin=vin)
    else:
        car = get_object_or_404(Car, vin=vin, seller=request.user)

    if request.method == "POST":
        try:
            new_stock = int(request.POST.get("stock", -1))
            if new_stock < 0:
                raise ValueError("Stock cannot be negative")
            old_stock = car.stock
            car.stock = new_stock
            car.save()  # save() also updates is_available via the Car.save() override
            ensure_primary_listing(car)
            log_activity(
                request.user,
                "Stock Updated",
                f"Stock of '{car.brand} {car.model}' (VIN: {car.vin}) updated from {old_stock} â†’ {new_stock} units."
            )
            messages.success(request, f"Stock updated to {new_stock} units successfully âœ…")
        except (ValueError, TypeError):
            messages.error(request, "Invalid stock value. Please enter a non-negative whole number. âŒ")

    return redirect("cars:inventory")

def compare_cars(request):
    compare_list = request.session.get("compare_list", [])
    cars = Car.objects.filter(id__in=compare_list)
    return render(request, "cars/compare.html", {"cars": cars})

def add_to_compare(request, car_id):
    compare_list = request.session.get("compare_list", [])

    if car_id not in compare_list:
        compare_list = (compare_list + [car_id])[-4:]
        request.session["compare_list"] = compare_list
        messages.success(request, "Car added to compare.")
    else:
        messages.info(request, "Already in compare list")

    return redirect("cars:compare_cars")

def remove_from_compare(request, car_id):
    compare_list = request.session.get("compare_list", [])
    if car_id in compare_list:
        compare_list.remove(car_id)
        request.session["compare_list"] = compare_list
        messages.success(request, "Removed from compare.")
    return redirect("cars:compare_cars")

@buyer_required
def ScheduleTestDriveView(request, vin):
    car = get_object_or_404(Car, vin=vin)
    listing = car.listings.first() # type: ignore
    
    if not listing:
        messages.error(request, "No active listing found for this vehicle.")
        return redirect("cars:car_detail", vin=vin)

    if request.user.role != User.Role.BUYER: # type: ignore
        messages.error(request, "Only registered buyers can request test drives.")
        return redirect("cars:car_detail", vin=vin)

    form = BuyerTestDriveForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        test_drive = form.save(commit=False)
        test_drive.listing = listing
        test_drive.buyer = request.user
        test_drive.status = "Pending"
        test_drive.save()

        # Task and Activity integration
        UserTask.objects.create(
            user=listing.seller,
            title=f"New Test Drive Request: {car.brand} {car.model}",
            description=f"Buyer {request.user.name} requested a test drive on {test_drive.proposed_date}.",
        )
        log_activity(request.user, "Test Drive Requested", f"Requested test drive for {car.brand} {car.model} on {test_drive.proposed_date}")
        
        # Email Notification
        try:
            email_subject = f"Test Drive Request: {car.brand} {car.model}"
            email_body = f"""
            Hello,
            
            A new test drive has been requested for your listing: {car.brand} {car.model}.
            
            Details:
            - Buyer: {request.user.name or request.user.email}
            - Proposed Date: {test_drive.proposed_date}
            
            Please log in to your dashboard to confirm or reschedule this request.
            
            Regards,
            The Vehicle Vault Team
            """
            
            # Send to seller
            EmailMessage(
                email_subject,
                email_body,
                settings.DEFAULT_FROM_EMAIL,
                [listing.seller.email]
            ).send(fail_silently=False)
            
            # Send confirmation to buyer
            EmailMessage(
                f"Confirmation: Test Drive Requested for {car.brand} {car.model}",
                f"Your request for a test drive on {test_drive.proposed_date} has been sent to the seller. You will be notified once they confirm.",
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email]
            ).send(fail_silently=False)
            
            messages.success(request, "Test drive requested successfully. Notifications have been sent. 📨")
        except Exception as e:
            print(f"Test drive email failure: {e}")
            messages.success(request, "Test drive requested successfully. The seller will confirm shortly. (Email notification pending) 🛡️")
        
        return redirect("cars:test_drives")

    return render(request, "testdrives/new.html", {
        "form": form,
        "car": car,
        "listing": listing
    })

@login_required
def TestDrivesView(request):
    if request.user.role not in [User.Role.BUYER, User.Role.SELLER, User.Role.ADMIN]:  # type: ignore
        messages.error(request, "You do not have access to test drive schedules.")
        return redirect("cars:home")

    if request.user.role == User.Role.BUYER: # type: ignore
        base_qs = (
            TestDrive.objects.filter(buyer=request.user)
            .select_related("listing__car", "listing__seller")
            .prefetch_related("listing__images")
        )
    elif request.user.role == User.Role.ADMIN: # type: ignore
        base_qs = (
            TestDrive.objects.all()
            .select_related("listing__car", "listing__seller", "buyer")
            .prefetch_related("listing__images")
        )
    else:
        base_qs = (
            TestDrive.objects.filter(listing__seller=request.user)
            .select_related("listing__car", "buyer")
            .prefetch_related("listing__images")
        )

    drives = base_qs.order_by("-created_at")
    
    stats = {
        "total": drives.count(),
        "pending": base_qs.filter(status="Pending").count(),
        "confirmed": base_qs.filter(status="Confirmed").count(),
    }

    return render(request, "testdrives/list.html", {
        "drives": drives,
        "stats": stats
    })

@login_required
def UpdateTestDriveStatusView(request, drive_id, status):
    drive = get_object_or_404(TestDrive, test_drive_id=drive_id)
    
    if drive.listing.seller != request.user and request.user.role != User.Role.ADMIN: # type: ignore
        messages.error(request, "Unauthorized access.")
        return redirect("cars:test_drives")

    valid_statuses = dict(TestDrive._meta.get_field("status").choices).keys() # type: ignore
    if status in valid_statuses:
        drive.status = status
        if status == "Confirmed" and not drive.actual_date:
            drive.actual_date = drive.proposed_date
        drive.save()
        UserTask.objects.create(
            user=drive.buyer,
            title=f"Test Drive {status}: {drive.listing.car.brand} {drive.listing.car.model}",
            description=f"Your test drive request for {drive.listing.car.brand} {drive.listing.car.model} is now {status}.",
        )
        log_activity(request.user, "Test Drive Updated", f"Status of test drive for {drive.listing.car} changed to '{status}'.")
        messages.success(request, f"Test drive status updated to {status}.")
    else:
        messages.error(request, "Invalid status update.")

    next_url = request.GET.get("next")
    if next_url:
        return redirect(next_url)
    return redirect("cars:test_drives")

@login_required
def PurchaseCarView(request, vin):
    car = get_object_or_404(Car, vin=vin)
    deal_id_str = request.GET.get('deal_id')
    
    # Validate deal_id is a valid UUID
    deal_id = None
    if deal_id_str:
        try:
            deal_id = uuid.UUID(deal_id_str)
        except (ValueError, TypeError):
            deal_id = None
    
    if request.user.role != User.Role.BUYER: # type: ignore

        messages.error(request, "Only buyers can purchase cars.")
        return redirect("cars:car_detail", vin=vin)
    
    # Honor negotiated deal price if active
    final_price = car.price
    if deal_id:
        active_deal = Deal.objects.filter(deal_id=deal_id, buyer=request.user, status='Accepted').first()

        if active_deal:
            final_price = active_deal.offered_price
            
    form = PurchaseForm(request.POST or None)

    def get_checkout_summary(current_form):
        payment_method = (
            current_form.data.get("payment_method")
            if request.method == "POST"
            else current_form.initial.get("payment_method", "Cash")
        ) or "Cash"
        is_token_booking = (
            current_form.data.get("is_token_booking") in ["on", "true", "True", "1"]
            if request.method == "POST"
            else False
        )
        emi_months = current_form.data.get("emi_months") if request.method == "POST" else current_form.initial.get("emi_months")
        down_payment_raw = current_form.data.get("down_payment") if request.method == "POST" else current_form.initial.get("down_payment")
        try:
            down_payment = float(down_payment_raw) if down_payment_raw not in [None, ""] else 0.0
        except (TypeError, ValueError):
            down_payment = 0.0

        gateway_amount = float(final_price)
        monthly_installment_preview = None
        total_payable_preview = float(final_price)

        if payment_method == "EMI" and emi_months:
            months = int(emi_months)
            principal = max(float(final_price) - down_payment, 0.0)
            annual_rate = 0.10
            r = annual_rate / 12
            if months > 0:
                if r > 0 and principal > 0:
                    monthly_installment_preview = principal * r * ((1 + r) ** months) / (((1 + r) ** months) - 1)
                elif months > 0:
                    monthly_installment_preview = principal / months
                if monthly_installment_preview is not None:
                    total_payable_preview = down_payment + (monthly_installment_preview * months)
            gateway_amount = down_payment if down_payment > 0 else float(final_price)

        if is_token_booking:
            gateway_amount = 50000.0

        return {
            "selected_payment_method": payment_method,
            "selected_is_token_booking": is_token_booking,
            "gateway_amount": gateway_amount,
            "down_payment_preview": down_payment,
            "emi_months_preview": emi_months,
            "monthly_installment_preview": monthly_installment_preview,
            "total_payable_preview": total_payable_preview,
        }
    
    if request.method == "POST" and form.is_valid():
        purchase = form.save(commit=False)
        purchase.user = request.user
        purchase.car = car
        purchase.price = final_price

        charge_amount = float(final_price)

        if purchase.payment_method == "EMI":
            purchase.is_emi = True
            months = int(form.cleaned_data["emi_months"])
            down_payment = float(form.cleaned_data["down_payment"])
            principal = float(final_price) - down_payment
            # Proper compound interest EMI formula: EMI = P * r(1+r)^n / ((1+r)^n - 1)
            annual_rate = 0.10  # 10% p.a.
            r = annual_rate / 12  # monthly rate
            n = months
            if r > 0:
                emi = principal * r * ((1 + r) ** n) / (((1 + r) ** n) - 1)
            else:
                emi = principal / n
            purchase.monthly_installment = float(f"{emi:.2f}")
            purchase.emi_months = months
            purchase.down_payment = down_payment
            charge_amount = down_payment

        if purchase.is_token_booking:
            charge_amount = 50000.00
        gateway = get_payment_gateway_credentials()
        key_id = gateway["key_id"]
        key_secret = gateway["key_secret"]
        if not payment_gateway_is_configured():
            messages.error(
                request,
                "Payment gateway is not configured yet. Add valid Razorpay credentials in admin or settings before accepting payments.",
            )
            return render(request, "cars/purchase_checkout.html", {
                "car": car,
                "form": form,
                "final_price": final_price,
                **get_checkout_summary(form),
            })

        # Initialize Razorpay Client
        client = razorpay.Client(auth=(key_id, key_secret))
        amount_in_paise = int(charge_amount * 100)

        try:
            # Generate official Razorpay Order
            razorpay_order = client.order.create({ # type: ignore
                "amount": amount_in_paise,
                "currency": 'INR',
                "payment_capture": '1'
            })
        except razorpay.errors.BadRequestError: # type: ignore
            messages.error(
                request,
                "Razorpay authentication failed. Please verify the configured key ID and key secret.",
            )
            return render(request, "cars/purchase_checkout.html", {
                "car": car,
                "form": form,
                "final_price": final_price,
                **get_checkout_summary(form),
            })

        purchase.razorpay_order_id = razorpay_order['id']
        purchase.payment_status = "Pending"
        purchase.save()
        log_activity(
            request.user,
            "Payment Initiated",
            f"Payment initiated for {car.brand} {car.model} with order {purchase.razorpay_order_id}.",
        )
        
        return render(request, "cars/razorpay_checkout.html", {
            "purchase": purchase,
            "razorpay_order_id": razorpay_order['id'],
            "razorpay_merchant_key": key_id,
            "payment_gateway_name": gateway["display_name"],
            "amount": charge_amount,
            "amount_in_paise": amount_in_paise,
            "car": car
        })

    return render(request, "cars/purchase_checkout.html", {
        "car": car,
        "form": form,
        "final_price": final_price,
        **get_checkout_summary(form),
    })

@login_required
def RazorpayCallbackView(request):
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id', '')
        order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')
        purchase_id = request.POST.get('purchase_id', '')
        
        if not all([payment_id, order_id, signature, purchase_id]):
            messages.error(request, "Invalid gateway payload.")
            return redirect("core:buyer_dashboard")
            
        purchase = get_object_or_404(Purchase, purchase_id=purchase_id)
        
        gateway = get_payment_gateway_credentials()
        key_id = gateway["key_id"]
        key_secret = gateway["key_secret"]
        if not payment_gateway_is_configured():
            messages.error(request, "Payment gateway is not configured correctly.")
            purchase.payment_status = "Cancelled"
            purchase.save()
            return redirect("cars:car_detail", vin=purchase.car.vin)

        client = razorpay.Client(auth=(key_id, key_secret))
        try:
            client.utility.verify_payment_signature({ # type: ignore
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            })
            
            # Signature Verified Successfully
            purchase.razorpay_payment_id = payment_id
            purchase.razorpay_signature = signature
            purchase.payment_status = "Completed"
            purchase.save()
            
            # Inventory Automation
            car = purchase.car
            log_activity(
                purchase.user,
                "Payment Verified",
                f"Payment verified for {car.brand} {car.model} with gateway payment {payment_id}.",
            )
            if car.stock > 0:
                car.stock -= 1
                car.save()
                
            # Mark listing as Sold (unless it's just a token booking and not full acquisition)
            listing = car.listings.first() # type: ignore
            if listing and not purchase.is_token_booking:
                listing.status = "Sold"
                listing.save()
                
            # Executive Invoicing Automation
            amount_secured = (
                50000.00
                if purchase.is_token_booking
                else float(purchase.down_payment) if purchase.is_emi and purchase.down_payment
                else float(purchase.price)
            )
                
            ctx = {
                'user_name': purchase.user.name or purchase.user.email,
                'car_brand': car.brand,
                'car_model': car.model,
                'car_vin': car.vin,
                'purchase': purchase,
                'amount': amount_secured
            }
            
            html_content = render_to_string('cars/emails/invoice.html', ctx)
            
            # Dispatch to Buyer
            msg_buyer = EmailMultiAlternatives(
                subject=f"Vault Authorization Verified: {car.brand} {car.model}",
                body="Your transaction has been securely captured.",
                from_email=settings.EMAIL_HOST_USER,
                to=[purchase.user.email]
            )
            msg_buyer.attach_alternative(html_content, "text/html")
            msg_buyer.send(fail_silently=True)
            
            # Dispatch to Seller / Logistics
            seller_email = listing.seller.email if listing else "admin@vehiclevault.com"
            msg_seller = EmailMultiAlternatives(
                subject=f"Asset Secured Alert: {car.brand} {car.model} Acquired",
                body="A client has successfully captured this asset via the Vault Payment Protocol.",
                from_email=settings.EMAIL_HOST_USER,
                to=[seller_email]
            )
            msg_seller.attach_alternative(html_content, "text/html")
            msg_seller.send(fail_silently=True)
            log_activity(
                purchase.user,
                "Receipt Generated",
                f"Receipt generated for {car.brand} {car.model} purchase {purchase.purchase_id}.",
            )
                  
            messages.success(request, f"Payment verified successfully for {car.brand} {car.model}.")
            # Log payment success for both buyer and seller
            log_activity(purchase.user, "Payment Completed", f"Payment secured for {car.brand} {car.model} (Rs. {purchase.price}).")
            if listing and listing.seller:
                log_activity(listing.seller, "Asset Sold", f"{car.brand} {car.model} acquired by {purchase.user.name or purchase.user.email} for Rs. {purchase.price}.")
            success_url = reverse("cars:purchase_success", kwargs={"purchase_id": purchase.purchase_id})
            return redirect(f"{success_url}?auto_receipt=1")
            
        except razorpay.errors.BadRequestError: # type: ignore
            messages.error(request, "Razorpay authentication failed during verification.")
            purchase.payment_status = "Cancelled"
            purchase.save()
            return redirect("cars:car_detail", vin=purchase.car.vin)

        except razorpay.errors.SignatureVerificationError: # type: ignore
            messages.error(request, "Gateway signature verification failed. Transaction cancelled.")
            purchase.payment_status = "Cancelled"
            purchase.save()
            return redirect("cars:car_detail", vin=purchase.car.vin)

    return redirect("core:buyer_dashboard")

@login_required
def PurchaseSuccessView(request, purchase_id):
    purchase = get_object_or_404(Purchase, purchase_id=purchase_id)
    amount_paid_now = get_amount_paid_now(purchase)
    timeline = build_purchase_timeline(purchase)
    return render(request, "cars/purchase_success.html", {
        "purchase": purchase,
        "amount_paid_now": amount_paid_now,
        "timeline": timeline,
        "auto_receipt": request.GET.get("auto_receipt") == "1",
    })


@login_required
def DownloadReceiptView(request, purchase_id):
    purchase = get_object_or_404(Purchase, purchase_id=purchase_id)
    listing = purchase.car.listings.order_by("-created_at").first() # type: ignore

    is_allowed = (
        request.user == purchase.user
        or request.user.role == User.Role.ADMIN  # type: ignore
        or (listing is not None and listing.seller == request.user)
    )
    if not is_allowed:
        messages.error(request, "You are not authorized to download this receipt.")
        return redirect("cars:home")

    if purchase.payment_status != "Completed":
        messages.error(request, "Receipt will be available after payment confirmation.")
        return redirect("cars:purchase_success", purchase_id=purchase.purchase_id)

    amount_paid_now = get_amount_paid_now(purchase)
    receipt_html = render_to_string(
        "cars/receipt_download.html",
        {
            "purchase": purchase,
            "amount_paid_now": amount_paid_now,
            "listing": listing,
        },
        request=request,
    )
    response = HttpResponse(receipt_html, content_type="text/html; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="vehicle-vault-receipt-{purchase.purchase_id}.html"'
    return response

@login_required
def InboxView(request):
    # Get all unique users the current user has messaged or received messages from
    sent_to = Message.objects.filter(sender=request.user).values_list('recipient', flat=True)
    received_from = Message.objects.filter(recipient=request.user).values_list('sender', flat=True)
    
    user_ids = set(list(sent_to) + list(received_from))
    contacts = User.objects.filter(user_id__in=user_ids)
    
    return render(request, "messaging/inbox.html", {"contacts": contacts})

@login_required
def ChatView(request, other_user_id):
    other_user = get_object_or_404(User, user_id=other_user_id)
    listing_id = request.GET.get('listing_id')
    listing = None
    if listing_id:
        listing = get_object_or_404(CarListing, listing_id=listing_id)

    if request.method == "POST":
        content = request.POST.get('content')
        if content:
            Message.objects.create(
                sender=request.user,
                recipient=other_user,
                listing=listing,
                content=content
            )
            log_activity(request.user, "Message Sent", f"Sent message to {other_user.email}")
            return redirect('cars:chat', other_user_id=other_user_id)

    messages_list = Message.objects.filter(
        (Q(sender=request.user) & Q(recipient=other_user)) |
        (Q(sender=other_user) & Q(recipient=request.user))
    ).order_by('created_at')
    
    # Mark received messages as read
    Message.objects.filter(sender=other_user, recipient=request.user, is_read=False).update(is_read=True)
    
    # Active deal bridging
    active_deal = None
    buyer = request.user if request.user.role == 'Buyer' else other_user
    seller = request.user if request.user.role == 'Seller' else other_user
    
    if buyer.role == 'Buyer' and seller.role == 'Seller': # type: ignore
        deal_qs = Deal.objects.filter(buyer=buyer, listing__seller=seller).exclude(status__in=['Rejected', 'Cancelled']).order_by('-updated_at')
        if listing:
            deal_qs = deal_qs.filter(listing=listing)
        active_deal = deal_qs.first()
    
    return render(request, "messaging/chat.html", {
        "other_user": other_user,
        "chat_messages": messages_list,
        "listing": listing,
        "active_deal": active_deal
    })

@login_required
def ProposeDealView(request, listing_id):
    listing = get_object_or_404(CarListing, listing_id=listing_id)
    
    if request.method == "POST":
        offered_price = request.POST.get('offered_price')
        message = request.POST.get('message', '')
        
        deal = Deal.objects.create(
            listing=listing,
            buyer=request.user,
            offered_price=offered_price,
            message=message
        )
        
        # Create a task for the seller
        UserTask.objects.create(
            user=listing.seller,
            title=f"New Offer: {listing.car}",
            description=f"Buyer {request.user.name} offered â‚¹{offered_price}. Message: {message}",
        )
        
        log_activity(request.user, "Deal Proposed", f"Proposed â‚¹{offered_price} for {listing.car}")
        messages.success(request, "Proposal transmitted successfully! ðŸš€")
        return redirect('cars:car_detail', vin=listing.car.vin)

    return render(request, "deals/propose.html", {"listing": listing})

@login_required
def UpdateDealStatusView(request, deal_id, status):
    deal = get_object_or_404(Deal, deal_id=deal_id)
    
    # Authorized? (Seller of the listing or Buyer of the deal)
    if request.user != deal.listing.seller and request.user != deal.buyer:
        messages.error(request, "Unauthorized ðŸš«")
        return redirect('cars:all_cars')

    if status in Deal.Status.values:
        deal.status = status
        deal.save()
        
        # Log activity
        log_activity(request.user, "Deal Updated", f"Deal status changed to {status} for {deal.listing.car}")
        
        # If accepted, maybe update listing status?
        if status == Deal.Status.ACCEPTED:
            deal.listing.status = "Pending"
            deal.listing.save()
            messages.success(request, "Deal accepted! The listing is now PENDING. ðŸ¤")
        else:
            messages.info(request, f"Deal marked as {status}.")

    next_url = request.GET.get("next")
    if next_url:
        return redirect(next_url)
    return redirect('core:seller_dashboard' if request.user.role == 'Seller' else 'core:buyer_dashboard')

@seller_or_admin_required
def WithdrawListingView(request, listing_id):
    listing = get_object_or_404(CarListing, listing_id=listing_id)
    
    # Control
    if request.user != listing.seller and request.user.role != User.Role.ADMIN: # type: ignore
        messages.error(request, "Unauthorized ðŸš«")
        return redirect('cars:inventory')

    listing.status = "Withdrawn"
    listing.save()
    
    log_activity(request.user, "Listing Withdrawn", f"Withdrew {listing.car} from inventory.")
    messages.warning(request, "Listing has been successfully withdrawn. ðŸ—‘ï¸")
    return redirect('cars:inventory')


@admin_required
def ImportStaticCarsView(request):
    result = sync_static_inventory(request.user)
    log_activity(
        request.user,
        "Static Inventory Import",
        f"Imported showroom assets from static/images. Created {result['created']} and refreshed {result['updated']} vehicles.",
    )
    messages.success(
        request,
        f"Static showroom import completed. Created {result['created']} and refreshed {result['updated']} vehicles.",
    )
    return redirect("cars:inventory")


@login_required
def toggle_wishlist(request, car_id):
    """Add or remove a car from the user's wishlist. Returns to the page they came from."""
    car = get_object_or_404(Car, id=car_id)
    existing = Wishlist.objects.filter(user=request.user, car=car).first()

    if existing:
        existing.delete()
        messages.info(request, f"{car.brand} {car.model} removed from your wishlist.")
    else:
        Wishlist.objects.create(user=request.user, car=car)
        log_activity(request.user, "Wishlist Updated", f"Saved {car.brand} {car.model} to wishlist.")
        messages.success(request, f"{car.brand} {car.model} saved to your wishlist.")

    next_url = request.GET.get("next") or request.META.get("HTTP_REFERER") or "cars:all_cars"
    return redirect(next_url)


@login_required
def wishlist_page(request):
    """Show all cars saved in the buyer's wishlist."""
    items = Wishlist.objects.filter(user=request.user).select_related("car__category")
    return render(request, "cars/wishlist.html", {"wishlist_items": items})

