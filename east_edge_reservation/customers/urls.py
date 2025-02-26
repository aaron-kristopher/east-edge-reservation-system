from django.urls import path
from . import views

urlpatterns = [
    path("", views.customers, name="customers"),
    path(
        "make-reservation/",
        views.customer_reservations,
        name="customer_reservations",
    ),
    path("make-reservation/barbers", views.barbers, name="barbers"),
]
