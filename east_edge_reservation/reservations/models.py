from django.db import models
from datetime import timedelta
from barbers.models import Barber, BarberService
from customers.models import Customer


class Reservation(models.Model):
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
    end_datetime = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="End Time",
        help_text="Calculated based on services' estimated time",
    )

    def calculate_end_datetime(self):
        """
        Calculates the end time of the reservation based on the total estimated time of services.
        """
        total_estimated_time = sum(
            rs.barber_service.service.estimated_time
            for rs in self.reservation_services.all()
        )
        return self.start_datetime + timedelta(minutes=total_estimated_time)

    def save(self, *args, **kwargs):
        # Automatically calculate and set end_datetime
        self.end_datetime = self.calculate_end_datetime()
        super().save(*args, **kwargs)


class ReservationService(models.Model):
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        verbose_name="Reservation",
        related_name="reservation_services",
    )
    barber_service = models.ForeignKey(
        BarberService,
        on_delete=models.CASCADE,
        verbose_name="Barber Service",
        related_name="reservation_services",
    )

    def clean(self):
        """
        Ensure that the barber in the reservation matches the barber in the barber_service.
        """
        if self.reservation.barber != self.barber_service.barber:
            raise ValidationError(
                "The barber for this service does not match the barber in the reservation."
            )

    class Meta:
        unique_together = ("reservation", "barber_service")
