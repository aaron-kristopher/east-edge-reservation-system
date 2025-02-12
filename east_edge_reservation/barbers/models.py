from django.db import models


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
    service_name = models.CharField(max_length=100)
    price = models.FloatField()
    estimated_time = models.SmallIntegerField()

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
