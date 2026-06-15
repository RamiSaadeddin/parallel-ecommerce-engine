from django.contrib import admin

from .models import LoadBalanceLog, PerformanceLog


@admin.register(PerformanceLog)
class PerformanceLogAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "method",
        "endpoint",
        "response_time_ms",
        "status_code",
        "created_at",
    ]
    list_filter = ["method", "status_code"]


@admin.register(LoadBalanceLog)
class LoadBalanceLogAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "strategy",
        "request_type",
        "handled_by",
        "created_at",
    ]
    list_filter = ["strategy", "handled_by"]