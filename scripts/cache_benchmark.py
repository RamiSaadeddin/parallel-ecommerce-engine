import json
import os
import statistics
import sys
import time
from pathlib import Path

import requests


# ---------------------------------------------------------
# Make this script able to use Django cache
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.core.cache import cache  # noqa: E402


BASE_URL = "http://127.0.0.1:8000"
PRODUCTS_ENDPOINT = f"{BASE_URL}/api/products/"

CACHE_KEY = "active_products"
REQUEST_COUNT = 50

RESULTS_DIR = PROJECT_ROOT / "benchmark_results"
RESULTS_FILE = RESULTS_DIR / "cache_benchmark_result.json"


def measure_request():
    started_at = time.perf_counter()

    response = requests.get(
    PRODUCTS_ENDPOINT,
    timeout=10,
    headers={
        "X-Skip-Performance-Log": "true",
    },
)

    elapsed_ms = (time.perf_counter() - started_at) * 1000

    try:
        body = response.json()
    except ValueError:
        body = {}

    return {
        "status_code": response.status_code,
        "elapsed_ms": round(elapsed_ms, 2),
        "source": body.get("source", "unknown"),
    }


def summarize(results):
    times = [result["elapsed_ms"] for result in results]

    return {
        "requests": len(results),
        "average_ms": round(statistics.mean(times), 2),
        "median_ms": round(statistics.median(times), 2),
        "min_ms": round(min(times), 2),
        "max_ms": round(max(times), 2),
        "sources": list(sorted(set(result["source"] for result in results))),
        "failed_requests": len(
            [result for result in results if result["status_code"] >= 400]
        ),
    }


def run_before_redis_test():
    """
    Simulates no caching by deleting the products cache before every request.
    This forces Django to query PostgreSQL each time.
    """

    results = []

    print("Running BEFORE Redis benchmark...")
    print("Cache will be cleared before every request.")
    print("-" * 60)

    for index in range(REQUEST_COUNT):
        cache.delete(CACHE_KEY)

        result = measure_request()
        results.append(result)

        print(
            f"Before Redis request {index + 1:02d} | "
            f"{result['elapsed_ms']} ms | "
            f"source: {result['source']}"
        )

    return results


def run_after_redis_test():
    """
    Measures cached requests.
    The first request warms the Redis cache, then repeated requests should use Redis.
    """

    results = []

    print("\nRunning AFTER Redis benchmark...")
    print("Cache will be warmed once, then reused.")
    print("-" * 60)

    cache.delete(CACHE_KEY)

    warmup_result = measure_request()

    print(
        f"Warmup request | "
        f"{warmup_result['elapsed_ms']} ms | "
        f"source: {warmup_result['source']}"
    )

    for index in range(REQUEST_COUNT):
        result = measure_request()
        results.append(result)

        print(
            f"After Redis request {index + 1:02d} | "
            f"{result['elapsed_ms']} ms | "
            f"source: {result['source']}"
        )

    return results


def main():
    RESULTS_DIR.mkdir(exist_ok=True)

    before_results = run_before_redis_test()
    after_results = run_after_redis_test()

    before_summary = summarize(before_results)
    after_summary = summarize(after_results)

    improvement_percentage = (
        (before_summary["average_ms"] - after_summary["average_ms"])
        / before_summary["average_ms"]
    ) * 100

    final_result = {
        "endpoint": PRODUCTS_ENDPOINT,
        "request_count_per_test": REQUEST_COUNT,
        "before_redis": before_summary,
        "after_redis": after_summary,
        "improvement_percentage": round(improvement_percentage, 2),
    }

    with open(RESULTS_FILE, "w", encoding="utf-8") as file:
        json.dump(final_result, file, indent=4)

    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)

    print("\nBefore Redis:")
    print(json.dumps(before_summary, indent=4))

    print("\nAfter Redis:")
    print(json.dumps(after_summary, indent=4))

    print(f"\nImprovement: {round(improvement_percentage, 2)}%")
    print(f"Results saved to: {RESULTS_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()