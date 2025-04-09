from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import render, redirect
from barbers.models import Barber, Service
from reservations.models import Reservation
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.contrib.auth.models import User
from .forms import SignUpForm
from .models import Customer, UserModel, UserManagerModel
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from .backends import EmailBackend 


# Create your views here.


def customers(request):
    context = {"services": Service.objects.all(), "barbers": Barber.objects.all()}
    return render(request, "customers/index.html", context)


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
    if datetime:
        reservations = list(
            Reservation.objects.filter(barber__id=barber_id)
            .filter(start_datetime__gte=datetime)
            .filter(status="P")
            .values()
        )
        return JsonResponse(reservations, safe=False)
    elif barber_id:
        barbers = list(
            Barber.objects.filter(id=barber_id).values()
        )
        return JsonResponse(barbers, safe=False)
        
# View for customer signup
def customer_signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data.get("first_name")
            last_name = form.cleaned_data.get("last_name")
            email = form.cleaned_data.get("email")
            phone_number = form.cleaned_data.get("phone_number")
            password = form.cleaned_data.get("password")
            
            user = UserModel.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone_number,
                password=password
            )
            user.backend = "customers.backends.EmailBackend"
            login(request, user)
            return redirect('customers')
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {'form': form})


def customer_login(request):
    error_message = None
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        user = authenticate(request, email=email, password=password)

        if user is not None:
            user.backend = "customers.backends.EmailBackend"
            login(request, user)
            redirected_url = request.POST.get("next") or request.GET.get("next") or "reservation" 
            return redirect(redirected_url)
        else:
            error_message = "Invalid email or password."

    return render(request, "accounts/login.html", {'error': error_message})


def customer_logout(request): 
    if request.method == "POST":
        logout(request)
        return redirect('login')
    else:
        return redirect('customers')


@login_required
def reservation(request):
    context = {"services": Service.objects.all(), "barbers": Barber.objects.all()}
    return render(request, "customers/reservation.html", context)

