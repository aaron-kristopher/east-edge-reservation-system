from django.contrib import admin
from .models import Reservation, ReservationService

admin.site.register(Reservation)
admin.site.register(ReservationService)
