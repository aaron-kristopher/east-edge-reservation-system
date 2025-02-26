from django.urls import path
from . import views

urlpatterns = [
    path("", views.customers, name="customers"),
    path(
        "reservation/select",
        views.customer_reservations,
        name="customer_reservations",
    ),
    path(
        "reservation/schedule",
        views.reservation_schedule,
        name="reservation_schedule",
    ),
    path("api/barbers", views.barbers, name="barbers"),
    path("api/reservations", views.get_barber_reservations, name="reservations"),
]
