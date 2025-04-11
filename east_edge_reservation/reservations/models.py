from django.db import models
from django.utils.translation import gettext_lazy as _
from barbers.models import Barber, Service
from customers.models import UserModel
from django.utils import timezone 
from datetime import timedelta


class Reservation(models.Model):
    class ReservationStatus(models.TextChoices):
        COMPLETED = "C", _("Completed")
        CANCELLED = "X", _("Cancelled")
        REQUESTED = "R", _("Requested")
        ACCEPTED = "A", _("Accepted")
        DECLINED = "D", _("Declined")

    start_datetime = models.DateTimeField()
    barber = models.ForeignKey(
        Barber,
        on_delete=models.CASCADE,
        verbose_name="Barber",
        related_name="reservations",
    )
    reserved_by = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        verbose_name="Reserved By",
        related_name="reservations",
    )
    reserved_for_first_name = models.CharField(max_length=50, blank=True, null=True)
    reserved_for_last_name = models.CharField(max_length=50, blank=True, null=True)
    reserved_for_email = models.EmailField(blank=True, null=True)
    reserved_for_phone = models.CharField(max_length=11, blank=True, null=True)
    is_reserved_for_self = models.BooleanField(default=True)

    services = models.ManyToManyField(
        Service,
        verbose_name="Services",
        related_name="reservations",
        help_text="Services included in this reservation",
    )
    end_datetime = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="End Time",
        help_text="Calculated based on services' estimated time",
    )
    status = models.CharField(
        max_length=1,
        choices=ReservationStatus,
        default=ReservationStatus.REQUESTED,
    )

    def calculate_end_datetime(self):
        
        if not self.start_datetime:
            return None 
        start_time = timezone.localtime(self.start_datetime)
        total_duration_minutes = sum(service.estimated_time for service in self.services.all())

        return start_time + timedelta(minutes=total_duration_minutes)
    def reserved_for_name(self):
        if self.is_reserved_for_self and self.reserved_by:
             return f"{self.reserved_by.first_name or ''} {self.reserved_by.last_name or ''}".strip()
        return f"{self.reserved_for_first_name or ''} {self.reserved_for_last_name or ''}".strip()

    def __str__(self):
        reserved_name = self.reserved_for_name()
        datetime_str = timezone.localtime(self.start_datetime).strftime('%Y-%m-%d %I:%M %p') if self.start_datetime else 'N/A'
        return f"Reservation for {reserved_name} with {self.barber.first_name} at {datetime_str}"
