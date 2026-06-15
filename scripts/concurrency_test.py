import os
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests


# ---------------------------------------------------------
# Make this script able to use Django models
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.core.cache import cache  # noqa: E402
from products.models import Product  # noqa: E402


# ---------------------------------------------------------
# Test settings
# ---------------------------------------------------------
BASE_URL = "http://127.0.0.1:8000"

ORDER_ENDPOINT = f"{BASE_URL}/api/orders/create/"

# Change this if your test product has another ID.
PRODUCT_ID = 1

# We intentionally make stock smaller than the number of users.
# Example: 5 stock, 20 users.
# Correct behavior: only 5 orders succeed, 15 fail.
INITIAL_STOCK = 5

CONCURRENT_USERS = 20
QUANTITY_PER_ORDER = 1


def prepare_test_data():
    """
    Prepares one product for the concurrency test.
    This resets the stock so every test starts from a known state.
    """

    User = get_user_model()

    user = User.objects.first()
    if user is None:
        raise Exception(
            "No user found. Create a superuser first using: python manage.py createsuperuser"
        )

    product = Product.objects.filter(id=PRODUCT_ID).first()

    if product is None:
        raise Exception(
            f"No product found with id={PRODUCT_ID}. "
            "Create a product in Django admin first, or change PRODUCT_ID in this script."
        )

    product.stock_quantity = INITIAL_STOCK
    product.version = 0
    product.is_active = True
    product.save()

    cache.delete("active_products")

    print("Test data prepared:")
    print(f"Product ID: {product.id}")
    print(f"Product name: {product.name}")
    print(f"Initial stock: {product.stock_quantity}")
    print(f"Concurrent users: {CONCURRENT_USERS}")
    print(f"Quantity per order: {QUANTITY_PER_ORDER}")
    print("-" * 60)


def send_order_request(user_number, start_event):
    """
    Sends one order request.
    All threads wait for start_event so they begin at almost the same time.
    """

    payload = {
        "product_id": PRODUCT_ID,
        "quantity": QUANTITY_PER_ORDER,
    }

    start_event.wait()

    started_at = time.perf_counter()

    try:
        response = requests.post(
            ORDER_ENDPOINT,
            json=payload,
            timeout=20,
        )

        elapsed_ms = (time.perf_counter() - started_at) * 1000

        try:
            response_body = response.json()
        except ValueError:
            response_body = response.text

        return {
            "user": user_number,
            "status_code": response.status_code,
            "success": response.status_code == 201,
            "elapsed_ms": round(elapsed_ms, 2),
            "response": response_body,
        }

    except requests.exceptions.ConnectionError:
        return {
            "user": user_number,
            "status_code": None,
            "success": False,
            "elapsed_ms": None,
            "response": "Connection error. Make sure Django server is running.",
        }

    except requests.exceptions.RequestException as error:
        return {
            "user": user_number,
            "status_code": None,
            "success": False,
            "elapsed_ms": None,
            "response": str(error),
        }


def run_concurrency_test():
    prepare_test_data()

    start_event = threading.Event()
    results = []

    print("Creating concurrent requests...")
    print("Starting test now...")
    print("-" * 60)

    test_started_at = time.perf_counter()

    with ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
        futures = [
            executor.submit(send_order_request, user_number, start_event)
            for user_number in range(1, CONCURRENT_USERS + 1)
        ]

        # Release all workers at almost the same time.
        start_event.set()

        for future in as_completed(futures):
            results.append(future.result())

    total_elapsed_ms = (time.perf_counter() - test_started_at) * 1000

    successful_results = [result for result in results if result["success"]]
    failed_results = [result for result in results if not result["success"]]

    product = Product.objects.get(id=PRODUCT_ID)
    final_stock = product.stock_quantity

    expected_successful_orders = INITIAL_STOCK // QUANTITY_PER_ORDER
    expected_final_stock = INITIAL_STOCK - (
        expected_successful_orders * QUANTITY_PER_ORDER
    )

    print("Individual results:")
    print("-" * 60)

    for result in sorted(results, key=lambda item: item["user"]):
        message = result["response"]

        if isinstance(message, dict):
            message = message.get("message", message)

        print(
            f"User {result['user']:02d} | "
            f"Status: {result['status_code']} | "
            f"Success: {result['success']} | "
            f"Time: {result['elapsed_ms']} ms | "
            f"Message: {message}"
        )

    print("-" * 60)
    print("Summary:")
    print(f"Total requests: {CONCURRENT_USERS}")
    print(f"Successful orders: {len(successful_results)}")
    print(f"Failed orders: {len(failed_results)}")
    print(f"Initial stock: {INITIAL_STOCK}")
    print(f"Final stock in database: {final_stock}")
    print(f"Expected successful orders: {expected_successful_orders}")
    print(f"Expected final stock: {expected_final_stock}")
    print(f"Total test time: {round(total_elapsed_ms, 2)} ms")
    print("-" * 60)

    if len(successful_results) == expected_successful_orders and final_stock == expected_final_stock:
        print("TEST PASSED: Race condition was prevented. Stock is correct.")
    else:
        print("TEST FAILED: Stock/order count is not correct. Check concurrency logic.")


if __name__ == "__main__":
    run_concurrency_test()