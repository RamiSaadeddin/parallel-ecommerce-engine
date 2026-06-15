from django.core.cache import cache
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import LoadBalanceLog, PerformanceLog


LOAD_BALANCER_SERVERS = [
    "server-1",
    "server-2",
    "server-3",
]

LOAD_BALANCER_CACHE_KEY = "round_robin_server_index"


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