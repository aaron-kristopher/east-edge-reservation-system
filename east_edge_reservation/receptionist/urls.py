from django.urls import path, include
from . import views

urlpatterns = [
    path("user-admin/dashboard/", views.receptionist, name="dashboard"),
    # path("user-admin/reservations/", views.schedule, name="barber_customer_reservations"),
    path("user-admin/update-reservation/<int:reservation_id>/", views.update_reservation, name="update_reservation"),
    path("user-admin/get-reservation/<int:reservation_id>/", views.get_reservation, name="get_reservation"),
    path("user-admin/get-barber/<int:barber_id>/", views.get_barber, name="get_barber")
]
