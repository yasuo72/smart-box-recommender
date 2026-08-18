"""
Management command to populate sample products and boxes.

Idempotent — uses get_or_create, safe to run multiple times.

Usage:
    python manage.py seed_data
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from shipping.models import Box, Product


PRODUCTS = [
    {"name": "Wireless Mouse", "length": 12, "width": 6, "height": 4, "weight": 0.15},
    {"name": "Mechanical Keyboard", "length": 45, "width": 15, "height": 4, "weight": 0.9},
    {"name": "USB-C Hub", "length": 10, "width": 5, "height": 2, "weight": 0.12},
    {"name": "Monitor Stand", "length": 50, "width": 25, "height": 12, "weight": 3.5},
    {"name": "Webcam", "length": 8, "width": 5, "height": 5, "weight": 0.18},
    {"name": "Laptop (15-inch)", "length": 36, "width": 25, "height": 2, "weight": 2.0},
    {"name": "Desk Lamp", "length": 15, "width": 15, "height": 45, "weight": 1.8},
    {"name": "Phone Case", "length": 16, "width": 8, "height": 1, "weight": 0.05},
]

BOXES = [
    {"name": "Small Box", "length": 20, "width": 15, "height": 10, "max_weight": 2, "cost": 1.50},
    {"name": "Medium Box", "length": 35, "width": 25, "height": 15, "max_weight": 5, "cost": 3.00},
    {"name": "Large Box", "length": 50, "width": 35, "height": 25, "max_weight": 10, "cost": 5.50},
    {"name": "Extra Large Box", "length": 60, "width": 40, "height": 35, "max_weight": 20, "cost": 8.00},
    {"name": "Flat Box", "length": 45, "width": 35, "height": 5, "max_weight": 3, "cost": 2.50},
]


class Command(BaseCommand):
    help = "Populate the database with sample products and boxes."

    def handle(self, *args, **options):
        created_products = 0
        for p in PRODUCTS:
            _, created = Product.objects.get_or_create(
                name=p["name"],
                defaults={
                    "length": Decimal(str(p["length"])),
                    "width": Decimal(str(p["width"])),
                    "height": Decimal(str(p["height"])),
                    "weight": Decimal(str(p["weight"])),
                },
            )
            if created:
                created_products += 1

        created_boxes = 0
        for b in BOXES:
            _, created = Box.objects.get_or_create(
                name=b["name"],
                defaults={
                    "length": Decimal(str(b["length"])),
                    "width": Decimal(str(b["width"])),
                    "height": Decimal(str(b["height"])),
                    "max_weight": Decimal(str(b["max_weight"])),
                    "cost": Decimal(str(b["cost"])),
                },
            )
            if created:
                created_boxes += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {created_products} products and {created_boxes} boxes."
            )
        )
