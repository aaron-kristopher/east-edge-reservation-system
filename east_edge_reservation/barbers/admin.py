from django.contrib.admin import register
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now, timedelta
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import (
    MultipleRelatedDropdownFilter,
    RangeDateTimeFilter,
    RelatedDropdownFilter,
)
from unfold.decorators import action

from datetime import datetime

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


@action(
    description="Generate barber schedule for next week (Sunday to Saturday, 8 AM - 5:30 PM)"
)
def generate_weekly_schedule(modeladmin, request, queryset):
    today = now().date()

    # Find upcoming Sunday
    next_sunday = today + timedelta(days=(6 - today.weekday()) % 7)

    schedules = []

    for barber in queryset:
        for i in range(7):  # Generate schedules for 7 days (Sunday to Saturday)
            schedule_date = next_sunday + timedelta(days=i)

            start_time = datetime.combine(schedule_date, datetime.min.time()).replace(
                hour=8, minute=0, second=0
            )
            end_time = start_time + timedelta(hours=9, minutes=30)  # Ends at 8 PM
            schedules.append(
                Schedule(
                    barber=barber, start_datetime=start_time, end_datetime=end_time
                )
            )

    # Bulk create schedules
    Schedule.objects.bulk_create(schedules)

    modeladmin.message_user(
        request,
        f"Schedules created for {len(queryset)} barbers from {next_sunday} to {next_sunday + timedelta(days=6)}.",
    )


@register(Barber)
class BarberAdmin(ModelAdmin):
    list_display = ("first_name", "last_name")
    list_filter_submit = True
    list_filter = [
        ("services", MultipleRelatedDropdownFilterAND),
    ]

    actions = [generate_weekly_schedule]


@register(Service)
class ServiceAdmin(ModelAdmin):
    list_display = ("service_name", "price")


@register(Schedule)
class ScheduleAdmin(ModelAdmin):
    list_display = ("barber", "start_datetime", "end_datetime")

    list_filter_submit = True
    list_filter = (
        ("start_datetime", RangeDateTimeFilter),
        ("barber", RelatedDropdownFilter),
    )
