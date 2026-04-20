from django.core.management.base import BaseCommand
from cars.models import Car

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for c in Car.objects.all():
            print(f"ID:{c.id} | B:{c.brand} | M:{c.model} | VIN:{c.vin} | IMG:{c.car_image.name if c.car_image else 'None'}")
