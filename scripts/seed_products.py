import os
import sys
from pathlib import Path
from decimal import Decimal

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.core.cache import cache
from products.models import Product


def main():
    products_to_create = []

    existing_count = Product.objects.filter(name__startswith="Benchmark Product").count()

    if existing_count >= 1000:
        print(f"Benchmark products already exist: {existing_count}")
        return

    for index in range(1, 1001):
        products_to_create.append(
            Product(
                name=f"Benchmark Product {index}",
                description=(
                    "This is a benchmark product used to test Redis caching "
                    "performance with a larger product dataset."
                ),
                price=Decimal("100.00"),
                stock_quantity=100,
                is_active=True,
            )
        )

    Product.objects.bulk_create(products_to_create)

    cache.delete("active_products")

    print("Created 1000 benchmark products.")
    print("Product cache cleared.")


if __name__ == "__main__":
    main()