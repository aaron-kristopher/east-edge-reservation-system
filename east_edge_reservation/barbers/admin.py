from django.contrib import admin
from .models import Barber, Service, BarberService

# Register your models here.
admin.site.register(Barber)
admin.site.register(Service)
admin.site.register(BarberService)
