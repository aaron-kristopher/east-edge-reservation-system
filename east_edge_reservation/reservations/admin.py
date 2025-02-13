from django.contrib.admin import register
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import RangeDateTimeFilter, ChoicesDropdownFilter
from unfold.decorators import action
from .models import Reservation


@action(description="Set reservation status to complete")
def complete_reservation(modeladmin, request, queryset):
    queryset.update(status="C")

    modeladmin.message_user(
        request,
        f"Set reservation status for {len(queryset)} reservations to `Completed`. ",
    )


@action(description="Revert reservation status to pending")
def revert_reservation_status(modeladmin, request, queryset):
    queryset.update(status="P")

    modeladmin.message_user(
        request,
        f"Set reservation status for {len(queryset)} reservations to `Pending`. ",
    )


@register(Reservation)
class ReservationAdmin(ModelAdmin):
    serach_fiels = []
    autocomplete_fields = []
    list_filter_submit = True
    list_filter = (
        ("start_datetime", RangeDateTimeFilter),
        ("status", ChoicesDropdownFilter),
    )
    list_display = (
        "barber",
        "customer",
        "get_reserved_services",
        "get_reservation",
        "formatted_status",
    )

    def get_reserved_services(self, obj):
        """
        Creates a string for the different services reserved. This is required to display
        the services in the Django Admin.
        """
        return ", ".join(service.service_name for service in obj.services.all()[:3])

    def get_reservation(self, obj):
        return obj.start_datetime

    def formatted_status(self, obj):
        """
        Returns the status field with different colors depending on the value.
        """
        color_map = {
            "P": "color: #f3aa20; font-weight: 600;",  # Pending (Yellow)
            "C": "color: #2a9d8f; font-weight: 600;",  # Confirmed (Green)
        }
        style = color_map.get(obj.status, "color: black; font-weight: 600;")
        return format_html(
            '<span style="{}">{}</span>',
            style,
            obj.get_status_display(),
        )

    actions = [
        complete_reservation,
    ]

    formatted_status.short_description = "Status"
    get_reservation.short_description = "Date"
    get_reserved_services.short_description = "Services"
