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


class ResourceUsageLog(models.Model):
    class Status(models.TextChoices):
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        COMPLETED = "COMPLETED", "Completed"

    resource_name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=Status.choices)

    current_usage = models.PositiveIntegerField()
    max_capacity = models.PositiveIntegerField()

    message = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.resource_name} - {self.status}"