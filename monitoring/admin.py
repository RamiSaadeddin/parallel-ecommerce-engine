from django.contrib import admin

from .models import LoadBalanceLog, PerformanceLog, ResourceUsageLog


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


@admin.register(ResourceUsageLog)
class ResourceUsageLogAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "resource_name",
        "status",
        "current_usage",
        "max_capacity",
        "message",
        "created_at",
    ]
    list_filter = ["resource_name", "status"]