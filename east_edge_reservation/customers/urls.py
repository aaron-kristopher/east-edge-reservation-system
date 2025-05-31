from django.urls import path
from . import views

urlpatterns = [
    path("", views.customers, name="customers"),
    path(
        "reservation/schedule",
        views.reservation_schedule,
        name="reservation_schedule",
    ),
    path("api/barbers", views.barbers, name="barbers"),
    path("api/reservations", views.get_barber_reservations, name="reservations"),
    path("reservation/", views.reservation, name="reservation"),
    path("login/", views.customer_login, name="login"),
    path("logout/", views.customer_logout, name="logout"),
    path("signup/", views.customer_signup, name="signup"),
    path("profile/", views.customers_profile, name="profile"),
    path(
        "reservation/my-appointments",
        views.customer_reservations_view,
        name="customer_reservations_view",
    ),
    path(
        "cancel-reservation/<int:reservation_id>/",
        views.cancel_reservation,
        name="cancel_reservation",
    ),
]
