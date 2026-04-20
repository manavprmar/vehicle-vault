import os
import shutil
from django.core.management.base import BaseCommand
from django.core.files import File
from cars.models import User, Seller, CarCategory, Brand, Car, CarListing, DiscoveryPill
from django.conf import settings

class Command(BaseCommand):
    help = 'Populate the database with cars using images from static/images/'

    def handle(self, *args, **kwargs):
        self.stdout.write("Populating database...")

        # Create Seller User
        user, created = User.objects.get_or_create(email="seller@example.com", defaults={
            'name': 'Super Seller',
            'role': User.Role.SELLER,
            'is_active': True,
        })
        if created:
            user.set_password("password123")
            user.save()
            Seller.objects.create(user=user, dealership_name="Vault Motors", location="Mumbai")
        seller = user

        # Categories
        cat_sedan, _ = CarCategory.objects.get_or_create(name="Sedan")
        cat_suv, _ = CarCategory.objects.get_or_create(name="SUV")
        cat_hatchback, _ = CarCategory.objects.get_or_create(name="Hatchback")

        # Create discovery pills
        DiscoveryPill.objects.get_or_create(label="Under 10 Lakhs", filter_value="10L", pill_type="Budget")
        DiscoveryPill.objects.get_or_create(label="SUV", filter_value="SUV", pill_type="Body Type")
        DiscoveryPill.objects.get_or_create(label="Automatic", filter_value="Automatic", pill_type="Transmission")

        static_images_dir = os.path.join(settings.BASE_DIR, 'static', 'images')
        if not os.path.exists(static_images_dir):
            self.stdout.write(self.style.ERROR(f"Directory not found: {static_images_dir}"))
            return

        # Brand logos mapping
        brand_logos = {
            'Aston Martin': 'aston-martinlogo.avif',
            'Audi': 'audilogo.avif',
            'Bentley': 'bentleylogo.avif',
            'BMW': 'bmwlogo.avif',
            'BYD': 'bydlogo.avif',
            'Citroen': 'citroenlogo.avif',
            'Ferrari': 'ferrarilogo.avif',
            'Force': 'force-motorslogo.avif',
            'Honda': 'hondalogo.avif',
            'Hyundai': 'hyundailogo.avif',
            'Isuzu': 'isuzulogo.avif',
            'Jaguar': 'jaguarlogo.avif',
            'Jeep': 'jeeplogo.avif',
            'Kia': 'kialogo.avif',
            'Lamborghini': 'lamborghinilogo.avif',
            'Land Rover': 'land-roverlogo.avif',
            'Lexus': 'lexuslogo.avif',
            'Lotus': 'lotuslogo.avif',
            'Mahindra': 'mahindralogo.avif',
            'Maruti Suzuki': 'marutilogo.avif',
            'Maserati': 'maseratilogo.avif',
            'McLaren': 'mclarenlogo.avif',
            'Mercedes-Benz': 'mercedes-benzlogo.avif',
            'MG': 'mglogo.avif',
            'Mini': 'minilogo.avif',
            'Nissan': 'nissanlogo.avif',
            'Porsche': 'porschelogo.avif',
            'Renault': 'renaultlogo.avif',
            'Rolls-Royce': 'rolls-roycelogo.avif',
            'Skoda': 'skodalogo.avif',
            'Tata': 'tatalogo.avif',
            'Tesla': 'teslalogo.avif',
            'Toyota': 'toyotalogo.avif',
            'Vinfast': 'vinfastlogo.avif',
            'Volkswagen': 'volkswagenlogo.avif',
            'Volvo': 'volvologo.avif',
        }

        for brand_name, logo_filename in brand_logos.items():
            logo_path = os.path.join(static_images_dir, logo_filename)
            brand, b_created = Brand.objects.get_or_create(name=brand_name)
            if b_created and os.path.exists(logo_path):
                with open(logo_path, 'rb') as f:
                    brand.logo.save(logo_filename, File(f), save=True)

        # predefined car mappings
        cars_data = [
            {'img': 'Audi.jpg', 'brand': 'Audi', 'model': 'A4', 'category': cat_sedan, 'price': 4500000},
            {'img': 'BMW.jpg', 'brand': 'BMW', 'model': 'X5', 'category': cat_suv, 'price': 8500000},
            {'img': 'Kia.jpg', 'brand': 'Kia', 'model': 'Seltos', 'category': cat_suv, 'price': 1500000},
            {'img': 'MG.jpg', 'brand': 'MG', 'model': 'Hector', 'category': cat_suv, 'price': 1800000},
            {'img': 'Mahindra.jpg', 'brand': 'Mahindra', 'model': 'XUV700', 'category': cat_suv, 'price': 2200000},
            {'img': 'Mercedes.jpg', 'brand': 'Mercedes-Benz', 'model': 'C-Class', 'category': cat_sedan, 'price': 5500000},
            {'img': 'Nissan.jpg', 'brand': 'Nissan', 'model': 'Magnite', 'category': cat_suv, 'price': 900000},
            {'img': 'Swift.jpg', 'brand': 'Maruti Suzuki', 'model': 'Swift', 'category': cat_hatchback, 'price': 800000},
            {'img': 'Tata.jpg', 'brand': 'Tata', 'model': 'Nexon', 'category': cat_suv, 'price': 1200000},
            {'img': 'honda.jpg', 'brand': 'Honda', 'model': 'City', 'category': cat_sedan, 'price': 1400000},
        ]

        for data in cars_data:
            img_filename = data['img']
            img_path = os.path.join(static_images_dir, img_filename)
            if not os.path.exists(img_path):
                self.stdout.write(self.style.WARNING(f"Image {img_path} not found. Skipping {data['brand']}."))
                continue

            vin = f"VIN_{data['brand'][:3].upper()}_{data['model'][:3].upper()}_123"
            car, c_created = Car.objects.get_or_create(
                vin=vin,
                defaults={
                    'seller': seller,
                    'category': data['category'],
                    'brand': data['brand'],
                    'model': data['model'],
                    'price': data['price'],
                    'fuel_type': 'Petrol',
                    'transmission': 'Automatic',
                    'mileage': '15 kmpl',
                    'launch_year': 2023,
                    'stock': 5,
                    'horsepower': 150,
                    'torque': 250,
                    'top_speed': 180,
                }
            )

            if c_created:
                with open(img_path, 'rb') as f:
                    car.car_image.save(img_filename, File(f), save=True)

                CarListing.objects.create(
                    car=car,
                    seller=seller,
                    price=data['price'],
                    mileage=15000,
                    description=f"Beautiful {data['brand']} {data['model']} in pristine condition.",
                    status="Active"
                )
                self.stdout.write(self.style.SUCCESS(f"Created car {data['brand']} {data['model']}"))
            else:
                self.stdout.write(f"Car {data['brand']} already exists.")

        self.stdout.write(self.style.SUCCESS('Successfully populated database!'))
