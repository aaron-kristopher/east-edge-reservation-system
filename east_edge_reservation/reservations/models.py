from django.db import models
from django.utils.translation import gettext_lazy as _
from barbers.models import Barber, Service
from customers.models import UserModel


class Reservation(models.Model):
    class ReservationStatus(models.TextChoices):
        COMPLETED = "C", _("Completed")
        PENDING = "P", _("Pending")
        CANCELLED = "X", _("Cancelled")

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
        default=ReservationStatus.PENDING,
    )

    def reserved_for_name(self):
        return f"{self.reserved_for_first_name or ''} {self.reserved_for_last_name or ''}".strip()

    def __str__(self):
        return f"{self.barber.first_name}: Reservation for {self.reserved_for_name()}"
