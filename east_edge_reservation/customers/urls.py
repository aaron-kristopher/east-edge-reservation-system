from django.urls import path
from . import views

urlpatterns = [
    path("customers/", views.customers, name="customers"),
    path(
        "customers/reservation",
        views.customer_reservation,
        name="customer_reservation",
    ),
]
