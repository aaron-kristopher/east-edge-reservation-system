from django.shortcuts import render

# Create your views here.


def customers(request):
    return render(request, "customers/index.html")


def customer_reservations(request):
    return render(request, "customers/reservations.html")

