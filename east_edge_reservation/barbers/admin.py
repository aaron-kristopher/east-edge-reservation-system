from django.contrib.admin import register
from unfold.admin import ModelAdmin
from .models import Barber, Service


@register(Barber)
class BarberAdmin(ModelAdmin):
    pass


@register(Service)
class ServiceAdmin(ModelAdmin):
    pass
