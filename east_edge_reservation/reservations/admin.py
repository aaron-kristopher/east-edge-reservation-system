from django.contrib.admin import register
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import RangeDateTimeFilter
from .models import Reservation


@register(Reservation)
class ReservationAdmin(ModelAdmin):
    list_filter_submit = True
    list_filter = (("start_datetime", RangeDateTimeFilter),)
    list_display = ("barber", "customer", "get_reserved_services", "get_reservation")

    def get_reserved_services(self, obj):
        """
        Creates a string for the different services reserved. This is required to display
        the services in the Django Admin.
        """
        return ", ".join(service.service_name for service in obj.services.all()[:3])

    def get_reservation(self, obj):
        return obj.start_datetime

    get_reservation.short_description = "Date"
    get_reserved_services.short_description = "Services"
