from django.urls import path, include
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
    path("reservation/", views.reservation, name="reservation"),

    path("login/", views.customer_login, name="login"),
    path("logout/", views.customer_logout, name="logout"),
    path("signup/", views.customer_signup, name="signup"),
    path("profile/", views.customers_profile, name="profile")

]
