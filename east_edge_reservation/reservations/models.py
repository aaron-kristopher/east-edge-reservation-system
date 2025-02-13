from django.db import models
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
from barbers.models import Barber, Service
from customers.models import Customer


class Reservation(models.Model):
    class ReservationStatus(models.TextChoices):
        COMPLETED = "C", _("Completed")
        PENDING = "P", _("Pending")

    start_datetime = models.DateTimeField()
    barber = models.ForeignKey(
        Barber,
        on_delete=models.CASCADE,
        verbose_name="Barber",
        related_name="reservations",
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        verbose_name="Customer",
        related_name="reservations",
    )
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

    def save(self, *args, **kwargs):
        """
        Overrides the save method to update end_datetime.
        Ensures the object is saved first before calculating the end_datetime.
        """
        super().save(*args, **kwargs)  # Save the instance to generate an ID
        self.update_end_datetime()  # Update end_datetime based on services
        super().save(*args, **kwargs)  # Save again to persist the changes

    def update_end_datetime(self):
        """
        Updates the reservation's end_datetime based on all selected services.
        """
        total_estimated_time = sum(
            service.estimated_time for service in self.services.all()
        )
        self.end_datetime = self.start_datetime + timedelta(
            minutes=total_estimated_time
        )

    def __str__(self):
        return f"{self.barber.first_name}: Reservation for {self.customer.first_name}"
