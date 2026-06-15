import time
from datetime import datetime, time as datetime_time
from decimal import Decimal

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date

from .models import DailySalesReport, Invoice, Order


@shared_task(bind=True, max_retries=3)
def generate_invoice_task(self, order_id):
    """
    Background task for generating an invoice after an order is created.

    This simulates an asynchronous operation that should not block
    the user's order request.
    """

    try:
        # Simulate a slow external/background operation.
        # This makes it clear in the demo that invoice generation is async.
        time.sleep(2)

        with transaction.atomic():
            order = Order.objects.get(id=order_id)

            invoice, created = Invoice.objects.get_or_create(
                order=order,
                defaults={
                    "invoice_number": f"INV-{order.id:06d}",
                },
            )

        return {
            "created": created,
            "order_id": order.id,
            "invoice_number": invoice.invoice_number,
        }

    except Order.DoesNotExist:
        return {
            "error": f"Order with id={order_id} does not exist"
        }

    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)


@shared_task(bind=True, max_retries=3)
def process_daily_sales_report_task(self, report_date=None, chunk_size=50):
    """
    Background batch-processing task.

    It processes paid orders for a specific day in chunks instead of loading
    and processing everything as one large operation.
    """

    try:
        chunk_size = int(chunk_size)

        if chunk_size <= 0:
            chunk_size = 50

        if report_date:
            parsed_report_date = parse_date(report_date)

            if parsed_report_date is None:
                return {
                    "error": "Invalid report_date format. Use YYYY-MM-DD."
                }
        else:
            parsed_report_date = timezone.localdate()

        day_start = timezone.make_aware(
            datetime.combine(parsed_report_date, datetime_time.min)
        )

        day_end = timezone.make_aware(
            datetime.combine(parsed_report_date, datetime_time.max)
        )

        paid_orders = Order.objects.filter(
            status=Order.Status.PAID,
            created_at__gte=day_start,
            created_at__lte=day_end,
        ).order_by("id")

        total_orders = paid_orders.count()
        total_sales = Decimal("0.00")
        processed_orders = 0
        processed_chunks = 0

        # Process data in chunks.
        for start in range(0, total_orders, chunk_size):
            chunk = list(paid_orders[start:start + chunk_size])

            chunk_total = sum(
                order.total_amount for order in chunk
            )

            total_sales += chunk_total
            processed_orders += len(chunk)
            processed_chunks += 1

            # Small delay to make the batch process visible in Celery logs.
            time.sleep(0.2)

        report, created = DailySalesReport.objects.update_or_create(
            report_date=parsed_report_date,
            defaults={
                "total_orders": processed_orders,
                "total_sales": total_sales,
                "processed_chunks": processed_chunks,
                "chunk_size": chunk_size,
            },
        )

        return {
            "created": created,
            "report_id": report.id,
            "report_date": str(report.report_date),
            "total_orders": report.total_orders,
            "total_sales": str(report.total_sales),
            "processed_chunks": report.processed_chunks,
            "chunk_size": report.chunk_size,
        }

    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)