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

    def update_end_datetime(self):
        """
        Updates the reservation's end_datetime based on all related ReservationServices.
        """
        total_estimated_time = sum(
            rs.barber_service.service.estimated_time
            for rs in self.reservation_services.all()
        )
        self.end_datetime = self.start_datetime + timedelta(
            minutes=total_estimated_time
        )
        self.save()

    def __str__(self):
        return f"[{self.barber.first_name}]: Reservation for {self.customer.first_name}"


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

    def save(self, *args, **kwargs):
        """
        Overrides the save method to update the reservation's end_datetime
        whenever a ReservationService is added or modified.
        """
        super().save(*args, **kwargs)  # Save the instance first
        self.reservation.update_end_datetime()  # Update the reservation's end time

    def clean(self):
        """
        Ensure that the barber in the reservation matches the barber in the barber_service.
        """
        if self.reservation.barber != self.barber_service.barber:
            raise ValidationError(
                "The barber for this service does not match the barber in the reservation."
            )

    def __str__(self):
        return f"Reservation {self.reservation.id}: {self.barber_service.service.service_name}"

    class Meta:
        unique_together = ("reservation", "barber_service")
