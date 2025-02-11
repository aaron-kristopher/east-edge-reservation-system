from django.shortcuts import render
from .models import Barber, Service


def barbers(request):
    barbers = Barber.objects.all()
    context = {"barbers": barbers}
    return render(request, "barbers/index.html", context)


def services(request):
    services = Service.objects.all()
    context = {"services": services}
    return render(request, "services/index.html", context)
