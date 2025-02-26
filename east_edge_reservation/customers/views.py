from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import render
from barbers.models import Barber, Service
from reservations.models import Reservation

# Create your views here.


def customers(request):
    return render(request, "customers/index.html")


def customer_reservations(request):
    context = {"services": Service.objects.all(), "barbers": Barber.objects.all()}
    return render(request, "customers/reservation_select.html", context)


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


def reservation_schedule(request):
    return render(request, "customers/reservation_schedule.html")


def get_barber_reservations(request):
    barber_id = int(request.GET.get("id"))
    datetime = request.GET.get("datetime")

    reservations = list(
        Reservation.objects.filter(barber__id=barber_id)
        .filter(start_datetime__gte=datetime)
        .filter(status="P")
        .values()
    )

    return JsonResponse(reservations, safe=False)
