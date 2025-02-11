from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import Reservation


@receiver(m2m_changed, sender=Reservation.services.through)
def update_end_datetime_on_services_change(sender, instance, action, **kwargs):
    """
    Updates the end_datetime of the reservation when services are added, removed, or cleared.
    """
    if action in ["post_add", "post_remove", "post_clear"]:
        instance.end_datetime = instance.calculate_end_datetime()
        instance.save()
