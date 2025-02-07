from django.shortcuts import render
from .models import Barber, Service, BarberService


def barbers(request):
    barbers = Barber.objects.all()
    context = {"barbers": barbers}
    return render(request, "barbers/index.html", context)


def services(request):
    services = Service.objects.all()
    context = {"services": services}
    return render(request, "services/index.html", context)


def services_view(request):
    services = Service.objects.all()  # Get all services
    barber_services = BarberService.objects.select_related(
        "barber", "service"
    )  # Preload related data
    service_with_barbers = {}  # Dictionary to store barbers for each service

    for service in services:
        # Filter barbers offering this service
        service_with_barbers[service] = barber_services.filter(service=service)

    return render(
        request,
        "services/barber-service.html",
        {"service_with_barbers": service_with_barbers},
    )
