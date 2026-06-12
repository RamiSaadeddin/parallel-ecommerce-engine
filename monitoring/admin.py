from django.contrib import admin
from .models import PerformanceLog


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