from django.core.management.base import BaseCommand
from users.models import User
from customers.models import Customer
from products.models import Product
from stores.models import Store
from orders.models import Order
# from payment.models import Payment
from ads.models import Ad
from faker import Faker
import random

fake = Faker()

class Command(BaseCommand):
    help = 'Seed database with sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding data...')

        # Example: Create 10 users
        for _ in range(10):
            User.objects.create(username=fake.user_name(), email=fake.email())

        # Repeat similar logic for other models
        for _ in range(10):
            Customer.objects.create(name=fake.name(), email=fake.email())

        for _ in range(10):
            Product.objects.create(name=fake.word(), price=random.randint(10, 500))

        # Add stores, orders, payment, ads similarly...

        self.stdout.write(self.style.SUCCESS('Seeding complete.'))
