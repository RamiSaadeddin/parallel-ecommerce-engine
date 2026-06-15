from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from products.models import Product
from .models import DailySalesReport, Order, OrderItem, Payment
from .serializers import (
    CreateOrderSerializer,
    DailySalesReportSerializer,
    OrderSerializer,
)
from django.core.cache import cache
from .tasks import generate_invoice_task, process_daily_sales_report_task
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
@api_view(["POST"])
def process_daily_sales(request):
    report_date = request.data.get("report_date")
    chunk_size = request.data.get("chunk_size", 50)

    try:
        chunk_size = int(chunk_size)

        if chunk_size <= 0:
            return Response(
                {
                    "message": "chunk_size must be greater than 0",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    except ValueError:
        return Response(
            {
                "message": "chunk_size must be a valid number",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    task = process_daily_sales_report_task.delay(
        report_date=report_date,
        chunk_size=chunk_size,
    )

    return Response(
        {
            "message": "Daily sales batch processing started",
            "task_id": task.id,
            "report_date": report_date or "today",
            "chunk_size": chunk_size,
        },
        status=status.HTTP_202_ACCEPTED,
    )
@api_view(["GET"])
def daily_sales_reports(request):
    reports = DailySalesReport.objects.all()
    serializer = DailySalesReportSerializer(reports, many=True)

    return Response(
        {
            "message": "Daily sales reports fetched successfully",
            "count": reports.count(),
            "data": serializer.data,
        }
    )