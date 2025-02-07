from django.urls import path
from . import views

urlpatterns = [
    path("barbers/", views.barbers, name="barbers"),
    path("services/", views.services, name="services"),
    path(
        "services/barber-service/", views.services_view, name="barber-service"
    ),  # Barber services page
]
