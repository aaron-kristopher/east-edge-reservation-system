from django.urls import path
from . import views

urlpatterns = [
    path("", views.customers, name="customers"),
    path(
        "customers/reservations",
        views.customer_reservations,
        name="customer_reservations",
    ),
]
