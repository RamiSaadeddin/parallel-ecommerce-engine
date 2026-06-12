from django.urls import path

from .views import create_order, order_list

urlpatterns = [
    path("", order_list, name="order-list"),
    path("create/", create_order, name="create-order"),
]