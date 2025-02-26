from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import render
from barbers.models import Barber, Service

# Create your views here.


def customers(request):
    return render(request, "customers/index.html")


def customer_reservations(request):
    context = {"services": Service.objects.all(), "barbers": Barber.objects.all()}
    return render(request, "customers/reservations.html", context)


def barbers(request):
    ids = request.GET.get("ids")
    ids = [int(i) for i in ids.split(",")]
    print(ids)
    barbers = list(
        Barber.objects.annotate(
            matching_services=Count("services", filter=Q(services__id__in=ids))
        )
        .filter(matching_services=len(ids))
        .values()
    )
    return JsonResponse(barbers, safe=False)
