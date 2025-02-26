from django.db import models
from django.utils.translation import gettext_lazy as _


class Barber(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=11)
    services = models.ManyToManyField(
        "Service", verbose_name="Services Offered", related_name="barbers"
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Service(models.Model):
    class ServiceCategory(models.TextChoices):
        HAIR = "H", _("Hair Services")
        NAIL = "N", _("Nail Services")
        GROOM = "G", _("Grooming Services")

    service_name = models.CharField(max_length=100)
    price = models.FloatField()
    estimated_time = models.SmallIntegerField()
    category = models.CharField(
        max_length=1, choices=ServiceCategory, default=ServiceCategory.HAIR
    )

    def __str__(self):
        return f"{self.service_name} - {self.price} PHP ({self.estimated_time} mins)"


class Schedule(models.Model):
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    barber = models.ForeignKey(Barber, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.start_datetime} - {self.start_datetime}"

    class Meta:
        ordering = ["start_datetime"]
