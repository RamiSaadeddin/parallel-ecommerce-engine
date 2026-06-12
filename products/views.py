from django.core.cache import cache
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Product
from .serializers import ProductSerializer


PRODUCTS_CACHE_KEY = "active_products"
PRODUCTS_CACHE_TIMEOUT = 60  # seconds


@api_view(["GET"])
def product_list(request):
    cached_products = cache.get(PRODUCTS_CACHE_KEY)

    if cached_products is not None:
        return Response({
            "message": "Products fetched successfully",
            "source": "redis_cache",
            "count": len(cached_products),
            "data": cached_products,
        })

    products = Product.objects.filter(is_active=True)
    serializer = ProductSerializer(products, many=True)

    data = list(serializer.data)

    cache.set(
        PRODUCTS_CACHE_KEY,
        data,
        timeout=PRODUCTS_CACHE_TIMEOUT,
    )

    return Response({
        "message": "Products fetched successfully",
        "source": "postgresql_database",
        "count": products.count(),
        "data": data,
    })