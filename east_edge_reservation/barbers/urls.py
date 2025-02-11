from django.urls import path
from . import views

urlpatterns = [
    path("barbers/", views.barbers, name="barbers"),
    path("services/", views.services, name="services"),
]
