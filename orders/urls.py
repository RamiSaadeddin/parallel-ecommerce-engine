from django.urls import path

from .views import (
    create_order,
    daily_sales_reports,
    order_list,
    process_daily_sales,
)

urlpatterns = [
    path("", order_list, name="order-list"),
    path("create/", create_order, name="create-order"),
    path("process-daily-sales/", process_daily_sales, name="process-daily-sales"),
    path("daily-sales-reports/", daily_sales_reports, name="daily-sales-reports"),
]