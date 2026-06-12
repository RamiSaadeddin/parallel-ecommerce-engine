from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import PerformanceLog


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