from django.urls import path

from .views import (
    load_balance_logs,
    performance_logs,
    simulate_load_balanced_order,
)

urlpatterns = [
    path("performance/", performance_logs, name="performance-logs"),
    path(
        "load-balanced-order/",
        simulate_load_balanced_order,
        name="load-balanced-order",
    ),
    path("load-balance-logs/", load_balance_logs, name="load-balance-logs"),
]