from django.contrib.admin import register
from unfold.admin import ModelAdmin
from .models import Customer


@register(Customer)
class CustomerAdmin(ModelAdmin):
    pass
