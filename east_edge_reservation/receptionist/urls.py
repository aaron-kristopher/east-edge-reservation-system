from django.urls import path, include
from . import views

urlpatterns = [
    path("user-admin/dashboard/", views.receptionist, name="dashboard"),
]
