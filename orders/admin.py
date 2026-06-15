from django.contrib import admin
from .models import Order, OrderItem, Payment, Invoice, DailySalesReport


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "status", "total_amount", "created_at"]
    list_filter = ["status"]
    inlines = [OrderItemInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "amount", "status", "created_at"]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "invoice_number", "generated_at"]


@admin.register(DailySalesReport)
class DailySalesReportAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "report_date",
        "total_orders",
        "total_sales",
        "processed_chunks",
        "chunk_size",
        "generated_at",
    ]
    list_filter = ["report_date"]