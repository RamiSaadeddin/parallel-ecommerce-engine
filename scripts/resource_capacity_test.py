import concurrent.futures
import time

import requests


URL = "http://127.0.0.1:8000/api/monitoring/resource-limited-task/"
CONCURRENT_USERS = 10


def send_request(index):
    started_at = time.perf_counter()

    response = requests.post(
        URL,
        timeout=15,
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
        "user": index,
        "status_code": response.status_code,
        "elapsed_ms": round(elapsed_ms, 2),
        "status": body.get("status", "unknown"),
        "message": body.get("message", ""),
    }


def main():
    print("=" * 60)
    print("RESOURCE CAPACITY TEST")
    print("=" * 60)
    print(f"Concurrent users: {CONCURRENT_USERS}")
    print("Maximum allowed simultaneous tasks: 3")
    print("-" * 60)

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=CONCURRENT_USERS
    ) as executor:
        futures = [
            executor.submit(send_request, index)
            for index in range(1, CONCURRENT_USERS + 1)
        ]

        results = [future.result() for future in futures]

    completed = [result for result in results if result["status_code"] == 200]
    rejected = [result for result in results if result["status_code"] == 429]

    for result in results:
        print(
            f"User {result['user']:02d} | "
            f"HTTP {result['status_code']} | "
            f"{result['elapsed_ms']} ms | "
            f"{result['status']} | "
            f"{result['message']}"
        )

    print("-" * 60)
    print(f"Completed tasks: {len(completed)}")
    print(f"Rejected tasks: {len(rejected)}")

    if len(completed) == 3 and len(rejected) == CONCURRENT_USERS - 3:
        print("TEST PASSED: Resource capacity limit was enforced.")
    else:
        print("TEST CHECK: Review results. Capacity behavior may need adjustment.")

    print("=" * 60)


if __name__ == "__main__":
    main()