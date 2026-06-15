import time

from .models import PerformanceLog


class PerformanceMonitoringMiddleware:
    """
    AOP-style middleware for performance monitoring.

    It wraps API requests, measures response time, and stores the result.
    This keeps performance monitoring separate from the business logic.

    During benchmarks, logging can be skipped by sending:
    X-Skip-Performance-Log: true

    This helps us measure the real endpoint performance without adding
    extra PostgreSQL writes from the monitoring system.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.perf_counter()

        response = self.get_response(request)

        end_time = time.perf_counter()
        response_time_ms = (end_time - start_time) * 1000

        try:
            skip_performance_log = (
                request.headers.get("X-Skip-Performance-Log", "").lower()
                == "true"
            )

            should_log = (
                request.path.startswith("/api/")
                and not request.path.startswith("/api/monitoring/")
                and not skip_performance_log
            )

            if should_log:
                PerformanceLog.objects.create(
                    endpoint=request.path,
                    method=request.method,
                    response_time_ms=round(response_time_ms, 2),
                    status_code=response.status_code,
                )

        except Exception:
            # Monitoring should never break the main application.
            pass

        return response