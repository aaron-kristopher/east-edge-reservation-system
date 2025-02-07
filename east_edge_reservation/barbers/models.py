from django.db import models


class Barber(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=11)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Service(models.Model):
    service_name = models.CharField(max_length=100)
    price = models.FloatField()
    estimated_time = models.SmallIntegerField()

    def __str__(self):
        return f"{self.service_name} - {self.price} PHP ({self.estimated_time} mins)"


class BarberService(models.Model):
    barber = models.ForeignKey(
        Barber,
        on_delete=models.CASCADE,
        verbose_name="Barber",
        related_name="services_offered",
    )

    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        verbose_name="Service",
        related_name="barbers",
    )

    def __str__(self):
        return f"{self.barber.first_name} {self.barber.last_name} - {self.service.service_name}"

    class Meta:
        unique_together = ("barber", "service")
