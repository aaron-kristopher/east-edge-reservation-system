from django.urls import path
from . import views

urlpatterns = [
    path('api/reservations/create/', views.create_reservation, name='create_reservation'),
]