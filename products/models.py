from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    # This is the important shared value.
    # Many users may try to reduce this number at the same time.
    stock_quantity = models.PositiveIntegerField(default=0)

    # We may use this later to explain optimistic locking.
    version = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.name} - Stock: {self.stock_quantity}"