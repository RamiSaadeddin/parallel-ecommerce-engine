import time

from django.core.cache import cache
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import LoadBalanceLog, PerformanceLog, ResourceUsageLog


LOAD_BALANCER_SERVERS = [
    "server-1",
    "server-2",
    "server-3",
]

LOAD_BALANCER_CACHE_KEY = "round_robin_server_index"

RESOURCE_NAME = "order_processing_slots"
RESOURCE_USAGE_CACHE_KEY = "resource_order_processing_current_usage"
RESOURCE_MAX_CAPACITY = 3
RESOURCE_PROCESSING_SECONDS = 3


@api_view(["GET"])
def performance_logs(request):
    logs = PerformanceLog.objects.all()[:50]

    data = []

    for log in logs:
        data.append({
            "id": log.id,
            "endpoint": log.endpoint,
            "method": log.method,
            "response_time_ms": log.response_time_ms,
            "status_code": log.status_code,
            "created_at": log.created_at,
        })

    return Response({
        "message": "Performance logs fetched successfully",
        "count": len(data),
        "data": data,
    })


@api_view(["POST"])
def simulate_load_balanced_order(request):
    """
    Simulates distributing incoming order requests across multiple backend servers
    using the Round Robin strategy.
    """

    current_index = cache.get(LOAD_BALANCER_CACHE_KEY, 0)

    selected_server = LOAD_BALANCER_SERVERS[current_index]

    next_index = (current_index + 1) % len(LOAD_BALANCER_SERVERS)
    cache.set(LOAD_BALANCER_CACHE_KEY, next_index, timeout=None)

    log = LoadBalanceLog.objects.create(
        strategy="round_robin",
        request_type="order_processing",
        handled_by=selected_server,
    )

    return Response({
        "message": "Order request distributed successfully",
        "strategy": "round_robin",
        "request_type": "order_processing",
        "handled_by": selected_server,
        "next_server_index": next_index,
        "available_servers": LOAD_BALANCER_SERVERS,
        "log_id": log.id,
        "explanation": (
            "This simulates a load balancer distributing incoming order "
            "requests across multiple backend servers using Round Robin."
        ),
    })


@api_view(["GET"])
def load_balance_logs(request):
    logs = LoadBalanceLog.objects.all()[:50]

    data = []

    for log in logs:
        data.append({
            "id": log.id,
            "strategy": log.strategy,
            "request_type": log.request_type,
            "handled_by": log.handled_by,
            "created_at": log.created_at,
        })

    return Response({
        "message": "Load balance logs fetched successfully",
        "count": len(data),
        "data": data,
    })


def get_current_resource_usage():
    return int(cache.get(RESOURCE_USAGE_CACHE_KEY, 0) or 0)


def release_resource_slot():
    try:
        remaining_usage = cache.decr(RESOURCE_USAGE_CACHE_KEY)
    except ValueError:
        cache.set(RESOURCE_USAGE_CACHE_KEY, 0, timeout=None)
        return 0

    if remaining_usage < 0:
        cache.set(RESOURCE_USAGE_CACHE_KEY, 0, timeout=None)
        return 0

    return remaining_usage


@api_view(["POST"])
def resource_limited_task(request):
    """
    Simulates resource/capacity management.

    Only a limited number of heavy order-processing tasks can run at the same time.
    Extra requests are rejected with 429 Too Many Requests.
    """

    cache.add(RESOURCE_USAGE_CACHE_KEY, 0, timeout=None)

    try:
        current_usage = cache.incr(RESOURCE_USAGE_CACHE_KEY)
    except ValueError:
        cache.set(RESOURCE_USAGE_CACHE_KEY, 1, timeout=None)
        current_usage = 1

    if current_usage > RESOURCE_MAX_CAPACITY:
        release_resource_slot()

        actual_usage = get_current_resource_usage()

        ResourceUsageLog.objects.create(
            resource_name=RESOURCE_NAME,
            status=ResourceUsageLog.Status.REJECTED,
            current_usage=actual_usage,
            max_capacity=RESOURCE_MAX_CAPACITY,
            message="Server capacity is full. Request was rejected.",
        )

        return Response(
            {
                "message": "Server capacity is full. Try again later.",
                "resource": RESOURCE_NAME,
                "status": "rejected",
                "current_usage": actual_usage,
                "max_capacity": RESOURCE_MAX_CAPACITY,
                "capacity": f"{actual_usage}/{RESOURCE_MAX_CAPACITY}",
                "explanation": (
                    "The system rejected this request because all available "
                    "order-processing slots are currently in use."
                ),
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    ResourceUsageLog.objects.create(
        resource_name=RESOURCE_NAME,
        status=ResourceUsageLog.Status.ACCEPTED,
        current_usage=current_usage,
        max_capacity=RESOURCE_MAX_CAPACITY,
        message="Task accepted because capacity was available.",
    )

    time.sleep(RESOURCE_PROCESSING_SECONDS)

    remaining_usage = release_resource_slot()

    ResourceUsageLog.objects.create(
        resource_name=RESOURCE_NAME,
        status=ResourceUsageLog.Status.COMPLETED,
        current_usage=remaining_usage,
        max_capacity=RESOURCE_MAX_CAPACITY,
        message="Task completed and resource slot was released.",
    )

    return Response({
        "message": "Resource-limited task completed successfully.",
        "resource": RESOURCE_NAME,
        "status": "completed",
        "processing_time_seconds": RESOURCE_PROCESSING_SECONDS,
        "max_capacity": RESOURCE_MAX_CAPACITY,
        "current_usage_after_release": remaining_usage,
        "explanation": (
            "This simulates capacity control by allowing only a limited "
            "number of heavy order-processing tasks to run at the same time."
        ),
    })


@api_view(["GET"])
def resource_usage_logs(request):
    logs = ResourceUsageLog.objects.all()[:50]

    data = []

    for log in logs:
        data.append({
            "id": log.id,
            "resource_name": log.resource_name,
            "status": log.status,
            "current_usage": log.current_usage,
            "max_capacity": log.max_capacity,
            "message": log.message,
            "created_at": log.created_at,
        })

    return Response({
        "message": "Resource usage logs fetched successfully",
        "count": len(data),
        "data": data,
    })