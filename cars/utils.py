from pathlib import Path
import re

from django.conf import settings
from django.db import OperationalError, ProgrammingError
from django.core.files import File
from django.utils.text import slugify

from cars.models import ActivityLog, Brand, Car, CarCategory, CarListing
from core.models import PaymentGatewaySettings


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".avif", ".gif"}
HERO_IMAGE_NAMES = {
    "hero-bg.jpg",
    "hero-bg2.jpg",
    "hero-bg3.jpg",
    "hero-bg4.jpg",
    "bg.jpg",
    "bg2.jpg",
    "bg_main.png",
}
GALLERY_EXCLUDE_PREFIXES = ("bg", "hero-bg", "logo", "placeholder")
BRAND_NAME_OVERRIDES = {
    "aston-martin": "Aston Martin",
    "audi": "Audi",
    "bentley": "Bentley",
    "bmw": "BMW",
    "byd": "BYD",
    "citroen": "Citroen",
    "ferrari": "Ferrari",
    "force-motors": "Force",
    "honda": "Honda",
    "hyundai": "Hyundai",
    "isuzu": "Isuzu",
    "jaguar": "Jaguar",
    "jeep": "Jeep",
    "kia": "Kia",
    "lamborghini": "Lamborghini",
    "land-rover": "Land Rover",
    "lexus": "Lexus",
    "lotus": "Lotus",
    "mahindra": "Mahindra",
    "maruti": "Maruti Suzuki",
    "maserati": "Maserati",
    "mclaren": "McLaren",
    "mercedes-benz": "Mercedes-Benz",
    "mg": "MG",
    "mini": "Mini",
    "nissan": "Nissan",
    "porsche": "Porsche",
    "renault": "Renault",
    "rolls-royce": "Rolls-Royce",
    "skoda": "Skoda",
    "tata": "Tata",
    "tesla": "Tesla",
    "toyota": "Toyota",
    "vinfast": "Vinfast",
    "volkswagen": "Volkswagen",
    "volvo": "Volvo",
}
STATIC_CAR_METADATA = {
    "audi.jpg": {"brand": "Audi", "model": "A4", "category": "Sedan", "price": 4500000},
    "bmw.jpg": {"brand": "BMW", "model": "X5", "category": "SUV", "price": 8500000},
    "kia.jpg": {"brand": "Kia", "model": "Seltos", "category": "SUV", "price": 1500000},
    "mg.jpg": {"brand": "MG", "model": "Hector", "category": "SUV", "price": 1800000},
    "mahindra.jpg": {"brand": "Mahindra", "model": "XUV700", "category": "SUV", "price": 2200000},
    "mercedes.jpg": {"brand": "Mercedes-Benz", "model": "C-Class", "category": "Sedan", "price": 5500000},
    "nissan.jpg": {"brand": "Nissan", "model": "Magnite", "category": "SUV", "price": 900000},
    "swift.jpg": {"brand": "Maruti Suzuki", "model": "Swift", "category": "Hatchback", "price": 800000},
    "tata.jpg": {"brand": "Tata", "model": "Nexon", "category": "SUV", "price": 1200000},
    "honda.jpg": {"brand": "Honda", "model": "City", "category": "Sedan", "price": 1400000},
    "download.jpg": {"brand": "Hyundai", "model": "Creta", "category": "SUV", "price": 1700000},
}


def _static_images_dir() -> Path:
    return settings.BASE_DIR / "static" / "images"


def _image_files():
    images_dir = _static_images_dir()
    if not images_dir.exists():
        return []
    return sorted(
        [
            image_path
            for image_path in images_dir.iterdir()
            if image_path.is_file() and image_path.suffix.lower() in IMAGE_EXTENSIONS
        ],
        key=lambda image_path: image_path.name.lower(),
    )


def _display_name_from_filename(stem: str) -> str:
    cleaned = stem.replace("-", " ").replace("_", " ").strip()
    return " ".join(part.upper() if part.isupper() else part.capitalize() for part in cleaned.split())


def get_static_gallery_images():
    gallery_images = []
    for image_path in _image_files():
        lower_name = image_path.name.lower()
        if "logo" in lower_name:
            continue
        if lower_name in HERO_IMAGE_NAMES:
            continue
        if any(lower_name.startswith(prefix) for prefix in GALLERY_EXCLUDE_PREFIXES):
            continue
        gallery_images.append(
            {
                "name": _display_name_from_filename(image_path.stem),
                "file": image_path.name,
            }
        )
    return gallery_images


def get_static_hero_images():
    hero_images = [
        {"name": _display_name_from_filename(image_path.stem), "file": image_path.name}
        for image_path in _image_files()
        if image_path.name.lower() in HERO_IMAGE_NAMES
    ]
    return hero_images


def get_static_brand_showcase(brands):
    static_logos = {}
    for image_path in _image_files():
        lower_name = image_path.name.lower()
        if "logo" not in lower_name:
            continue
        brand_key = lower_name.replace("logo", "").rsplit(".", 1)[0].strip("-_ ")
        brand_name = BRAND_NAME_OVERRIDES.get(brand_key, _display_name_from_filename(brand_key))
        static_logos[brand_name.lower()] = image_path.name

    showcase = []
    seen_names = set()

    for brand in brands:
        brand_name = brand.name.strip()
        seen_names.add(brand_name.lower())
        showcase.append(
            {
                "name": brand_name,
                "logo_url": brand.logo.url if getattr(brand, "logo", None) else None,
                "static_file": static_logos.get(brand_name.lower()),
            }
        )

    for brand_name, image_file in sorted(static_logos.items()):
        if brand_name in seen_names:
            continue
        showcase.append(
            {
                "name": BRAND_NAME_OVERRIDES.get(brand_name, _display_name_from_filename(brand_name)),
                "logo_url": None,
                "static_file": image_file,
            }
        )

    return showcase


def extract_numeric_mileage(mileage_value) -> int:
    if mileage_value is None:
        return 0
    match = re.search(r"\d+", str(mileage_value))
    return int(match.group()) if match else 0


def ensure_primary_listing(car, description=""):
    listing_defaults = {
        "seller": car.seller,
        "price": car.price,
        "mileage": extract_numeric_mileage(car.mileage),
        "description": description or f"{car.brand} {car.model} available in inventory.",
        "status": "Active" if car.stock > 0 else "Pending",
    }
    listing = CarListing.objects.filter(car=car).order_by("created_at").first()
    created = False
    if listing is None:
        listing = CarListing.objects.create(car=car, **listing_defaults)
        created = True

    updates = []
    if listing.price != car.price:
        listing.price = car.price
        updates.append("price")
    listing_mileage = extract_numeric_mileage(car.mileage)
    if listing.mileage != listing_mileage:
        listing.mileage = listing_mileage
        updates.append("mileage")
    target_status = "Active" if car.stock > 0 else "Pending"
    if listing.status != target_status:
        listing.status = target_status
        updates.append("status")
    if listing.seller_id != car.seller_id:
        listing.seller = car.seller
        updates.append("seller")
    if description and listing.description != description:
        listing.description = description
        updates.append("description")

    if updates:
        listing.save(update_fields=updates)

    return listing, created


def sync_static_inventory(owner):
    created_count = 0
    updated_count = 0
    imported_cars = []

    for image_path in _image_files():
        image_name = image_path.name.lower()
        metadata = STATIC_CAR_METADATA.get(image_name)
        if metadata is None:
            continue

        category, _ = CarCategory.objects.get_or_create(name=metadata["category"])
        Brand.objects.get_or_create(name=metadata["brand"])

        vin = f"STATIC-{slugify(metadata['brand'])[:20].upper()}-{slugify(metadata['model'])[:20].upper()}"
        car, car_created = Car.objects.get_or_create(
            vin=vin,
            defaults={
                "seller": owner,
                "category": category,
                "brand": metadata["brand"],
                "model": metadata["model"],
                "price": metadata["price"],
                "fuel_type": "Petrol",
                "transmission": "Automatic",
                "seating_capacity": 5,
                "mileage": "15 kmpl",
                "launch_year": 2025,
                "stock": 5,
                "is_available": True,
            },
        )

        car_updates = []
        if car.seller_id != owner.pk:
            car.seller = owner
            car_updates.append("seller")
        if car.category_id != category.id:
            car.category = category
            car_updates.append("category")
        if car.price != metadata["price"]:
            car.price = metadata["price"]
            car_updates.append("price")

        if car_updates:
            car.save(update_fields=car_updates)

        if not car.car_image:
            with image_path.open("rb") as image_file:
                car.car_image.save(image_path.name, File(image_file), save=True)

        _, listing_created = ensure_primary_listing(
            car,
            description=f"Static showroom import for {car.brand} {car.model}.",
        )

        imported_cars.append(car)
        if car_created or listing_created:
            created_count += 1
        else:
            updated_count += 1

    return {
        "created": created_count,
        "updated": updated_count,
        "cars": imported_cars,
    }


def get_payment_gateway_settings(provider=PaymentGatewaySettings.Provider.RAZORPAY):
    try:
        gateway = (
            PaymentGatewaySettings.objects.filter(provider=provider, is_active=True)
            .order_by("-updated_at")
            .first()
        )
        if gateway:
            return gateway
    except (ProgrammingError, OperationalError):
        # The table may not exist yet if migrations haven't been applied.
        return None
    return None


def get_payment_gateway_credentials(provider=PaymentGatewaySettings.Provider.RAZORPAY):
    gateway = get_payment_gateway_settings(provider=provider)
    if gateway and gateway.key_id and gateway.key_secret:
        return {
            "provider": gateway.provider,
            "display_name": gateway.display_name,
            "key_id": gateway.key_id,
            "key_secret": gateway.key_secret,
            "webhook_secret": gateway.webhook_secret,
            "sandbox_mode": gateway.sandbox_mode,
            "source": "database",
        }

    return {
        "provider": provider,
        "display_name": getattr(settings, "PAYMENT_GATEWAY_DISPLAY_NAME", "Vehicle Vault Payments"),
        "key_id": getattr(settings, "RAZORPAY_KEY_ID", ""),
        "key_secret": getattr(settings, "RAZORPAY_KEY_SECRET", ""),
        "webhook_secret": getattr(settings, "RAZORPAY_WEBHOOK_SECRET", ""),
        "sandbox_mode": getattr(settings, "PAYMENT_GATEWAY_SANDBOX_MODE", True),
        "source": "settings",
    }


def payment_gateway_is_configured(provider=PaymentGatewaySettings.Provider.RAZORPAY):
    gateway = get_payment_gateway_credentials(provider=provider)
    key_id = str(gateway.get("key_id", ""))
    key_secret = str(gateway.get("key_secret", ""))
    return bool(key_id and key_secret and "PLACEHOLDER" not in key_id.upper() and "PLACEHOLDER" not in key_secret.upper())


def log_activity(user, action_type, description):
    """
    Utility function to log user actions for the Executive Activity Stream.
    """
    if user.is_authenticated:
        ActivityLog.objects.create(
            user=user,
            action_type=action_type,
            description=description
        )
