from django.shortcuts import render

# Create your views here.


def customers(request):
    return render(request, "customers/index.html")


def customer_reservation(request):
    return render(request, "customers/reservation.html")

