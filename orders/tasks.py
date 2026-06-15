import time

from celery import shared_task
from django.db import transaction

from .models import Invoice, Order


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