from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()


@register.filter(name="filter_status")
def filter_status(reservations, statuses_str):
    status_list = [s.strip() for s in statuses_str.split(",")]
    return [r for r in reservations if r.status in status_list]


@register.filter(name="is_cancel_disabled")
def is_cancel_disabled(reservation_start_datetime):
    """
    Checks if the reservation start datetime is less than 24 hours from now.
    """
    if not reservation_start_datetime:
        return False  # Or True, depending on desired behavior for missing dates
    now = timezone.now()
    # Make reservation_start_datetime timezone-aware if it's naive, matching 'now'
    if timezone.is_naive(reservation_start_datetime):
        # Assuming your reservation_start_datetime is stored in settings.TIME_ZONE
        reservation_start_datetime = timezone.make_aware(
            reservation_start_datetime, timezone.get_current_timezone()
        )

    return reservation_start_datetime < (now + timedelta(days=1))


@register.filter(name="is_past_cancellation_window")
def is_past_cancellation_window(reservation_start_datetime):
    """
    Checks if the reservation start datetime is less than 1 day (24 hours) from now.
    Effectively, can the user still cancel?
    The condition is: reservation_time - now < 1 day
    """
    if not reservation_start_datetime:
        return False  # Should not happen with valid data
    now = timezone.now()
    # Ensure reservation_start_datetime is offset-aware for comparison
    if timezone.is_naive(reservation_start_datetime):
        reservation_start_datetime = timezone.make_aware(
            reservation_start_datetime, timezone.get_default_timezone()
        )

    return (reservation_start_datetime - now) < timedelta(days=1)

