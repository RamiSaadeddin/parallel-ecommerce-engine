from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from products.models import Product
from .models import Order, OrderItem, Payment
from .serializers import CreateOrderSerializer, OrderSerializer
from django.core.cache import cache
from .tasks import generate_invoice_task
from celery import shared_task
@api_view(["POST"])
def create_order(request):
    serializer = CreateOrderSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {
                "message": "Invalid order data",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    product_id = serializer.validated_data["product_id"]
    quantity = serializer.validated_data["quantity"]

    User = get_user_model()
    user = User.objects.first()

    if user is None:
        return Response(
            {
                "message": "No user found. Please create a superuser first using python manage.py createsuperuser.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        with transaction.atomic():
            # Synchronization point:
            # This locks the product row while the order is being created.
            # Later, with PostgreSQL, this prevents two users from reducing the same stock incorrectly.
            product = Product.objects.select_for_update().get(
                id=product_id,
                is_active=True,
            )

            if product.stock_quantity < quantity:
                return Response(
                    {
                        "message": "Not enough stock",
                        "available_stock": product.stock_quantity,
                        "requested_quantity": quantity,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            total_amount = product.price * quantity

            product.stock_quantity -= quantity
            product.version += 1
            product.save()
            # Clear products cache only after the transaction succeeds.
            transaction.on_commit(lambda: cache.delete("active_products"))

            order = Order.objects.create(
                user=user,
                status=Order.Status.PAID,
                total_amount=total_amount,
            )

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price_at_purchase=product.price,
            )

            Payment.objects.create(
                order=order,
                amount=total_amount,
                status=Payment.Status.SUCCESS,
            )

            # Queue invoice generation only after the database transaction succeeds.
            # This keeps invoice generation outside the main request path.
            transaction.on_commit(
    lambda: generate_invoice_task.delay(order.id),
    robust=True,
)

    except Product.DoesNotExist:
        return Response(
            {
                "message": "Product not found or inactive",
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    response_serializer = OrderSerializer(order)

    return Response(
        {
            "message": "Order created successfully",
            "remaining_stock": product.stock_quantity,
            "data": response_serializer.data,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
def order_list(request):
    orders = Order.objects.all()
    serializer = OrderSerializer(orders, many=True)

    return Response(
        {
            "message": "Orders fetched successfully",
            "count": orders.count(),
            "data": serializer.data,
        }
    )