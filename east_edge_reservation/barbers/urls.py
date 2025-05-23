from django.urls import path
from . import views

urlpatterns = [
    # path("barbers/", views.barbers, name="barbers"),
    # path("services/", views.services, name="services"),
    path(
        "api/available-times/",
        views.AvailableTimeSlotsView.as_view(),
        name="available-times",
    ),
    path("reservations/", views.schedule, name="barber_customer_reservations")
]
