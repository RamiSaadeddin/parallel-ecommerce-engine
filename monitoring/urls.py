from django.urls import path

from .views import performance_logs

urlpatterns = [
    path("performance/", performance_logs, name="performance-logs"),
]