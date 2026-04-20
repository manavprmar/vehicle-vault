from django.core.management.base import BaseCommand
from cars.models import Car, CarListing, Brand

class Command(BaseCommand):
    help = 'Aggressively removes duplicate cars and brands'

    def handle(self, *args, **kwargs):
        self.stdout.write("Finding duplicates...")
        
        seen_cars = {} # (brand, model) -> car_id
        cars_to_delete = []
        
        for car in Car.objects.all():
            # Clean brand and model for comparison
            b = car.brand.strip().lower()
            m = car.model.strip().lower().replace("model ", "")
            
            key = (b, m)
            if key in seen_cars:
                self.stdout.write(self.style.WARNING(f"Delete duplicate Car: {car.brand} {car.model} ({car.vin})"))
                cars_to_delete.append(car.id)
            else:
                seen_cars[key] = car.id

        # Delete in bulk
        if cars_to_delete:
            CarListing.objects.filter(car_id__in=cars_to_delete).delete()
            Car.objects.filter(id__in=cars_to_delete).delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted {len(cars_to_delete)} duplicate cars."))

        # Clean Brands as well
        seen_brands = {}
        brands_to_delete = []
        for brand in Brand.objects.all():
            b_name = brand.name.strip().lower()
            if b_name in seen_brands:
                brands_to_delete.append(brand.id)
                self.stdout.write(self.style.WARNING(f"Delete duplicate Brand: {brand.name}"))
            else:
                seen_brands[b_name] = brand.id
        
        if brands_to_delete:
            Brand.objects.filter(id__in=brands_to_delete).delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted {len(brands_to_delete)} duplicate brands."))
