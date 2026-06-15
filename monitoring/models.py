from django.db import models


class PerformanceLog(models.Model):
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)

    response_time_ms = models.FloatField()

    status_code = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.method} {self.endpoint} - {self.response_time_ms}ms"


class LoadBalanceLog(models.Model):
    strategy = models.CharField(max_length=50)
    request_type = models.CharField(max_length=100)
    handled_by = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.request_type} handled by {self.handled_by}"