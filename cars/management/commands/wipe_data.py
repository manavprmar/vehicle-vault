from django.core.management.base import BaseCommand
from cars.models import Car, CarListing, Brand

class Command(BaseCommand):
    help = 'Wipes all cars and listings to allow for a clean populate_data run'

    def handle(self, *args, **kwargs):
        self.stdout.write("Wiping all existing car data...")
        CarListing.objects.all().delete()
        Car.objects.all().delete()
        # Keep brands but clean them
        Brand.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Database wiped successfully!"))
