from django.contrib.admin import register
from unfold.admin import ModelAdmin
from .models import Reservation


@register(Reservation)
class ReservationAdmin(ModelAdmin):
    pass
