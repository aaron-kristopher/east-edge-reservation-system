from django.contrib.admin import register
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import MultipleRelatedDropdownFilter

from .models import Barber, Service, Schedule


class MultipleRelatedDropdownFilterAND(MultipleRelatedDropdownFilter):
    title = _("Services (AND)")  # Admin display name
    parameter_name = "services"

    def queryset(self, request, queryset):
        selected_services = self.value()  # Get selected service IDs

        if selected_services:
            # selected_services is already a list, no need to split
            service_ids = selected_services

            # Filter barbers who have ALL selected services using AND logic
            for service_id in service_ids:
                queryset = queryset.filter(services__id=service_id)

        return queryset


@register(Barber)
class BarberAdmin(ModelAdmin):
    list_display = ("first_name", "last_name")
    list_filter_submit = True
    list_filter = [
        ("services", MultipleRelatedDropdownFilterAND),
    ]


@register(Service)
class ServiceAdmin(ModelAdmin):
    list_display = ("service_name", "price")


@register(Schedule)
class ScheduleAdmin(ModelAdmin):
    list_display = ("barber", "start_datetime", "end_datetime")
