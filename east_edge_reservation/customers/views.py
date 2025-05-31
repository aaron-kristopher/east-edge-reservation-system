from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.shortcuts import get_object_or_404
from core.decorators import group_required

from barbers.models import Barber, Service
from .forms import UserProfileUpdateForm, UserEmailChangeForm
from .forms import SignUpForm
from .models import UserModel
from reservations.models import Reservation
from reservations.sms_utils import send_cancellation_sms

# Create your views here.


# @group_required('Customer')
def customers(request):
    context = {"services": Service.objects.all(), "barbers": Barber.objects.all()}
    return render(request, "customers/index.html", context)


# def customer_reservations(request):
#     context = {"services": Service.objects.all(), "barbers": Barber.objects.all()}
#     return render(request, "customers/reservation_select.html", context)


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
        barbers = list(Barber.objects.filter(id=barber_id).values())
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
                password=password,
            )

            # Add user to Customer group
            from django.contrib.auth.models import Group

            customer_group = Group.objects.get(name="Customer")
            user.groups.add(customer_group)

            user.backend = "customers.backends.EmailBackend"
            login(request, user)
            return redirect("customers")
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form})


def customer_login(request):
    error_message = None
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, email=email, password=password)

        if user is not None:
            user.backend = "customers.backends.EmailBackend"
            login(request, user)

            # Check if user is in the Receptionist group
            if user.groups.filter(name="Receptionist").exists():
                # Redirect to the receptionist dashboard
                return redirect("dashboard")
            else:
                # For regular customers, use the normal flow
                redirected_url = (
                    request.POST.get("next") or request.GET.get("next") or "reservation"
                )
                return redirect(redirected_url)
        else:
            error_message = "Invalid email or password."

    return render(request, "accounts/login.html", {"error": error_message})


def customer_logout(request):
    if request.method == "POST":
        logout(request)
        return redirect("customers")  # Redirect to the landing page for all users
    else:
        return redirect("customers")


@login_required
@group_required("Customer")
def reservation(request):
    context = {"services": Service.objects.all(), "barbers": Barber.objects.all()}
    return render(request, "customers/reservation.html", context)


@login_required
# Allow both customers and receptionists to access their profile
def customers_profile(request):
    user = request.user

    if request.method == "POST":
        form_type = request.POST.get("form_type")

        if form_type == "profile_update":
            profile_form = UserProfileUpdateForm(request.POST, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Your profile details have been updated.")
                return redirect("profile")
            else:
                for field, errors in profile_form.errors.items():
                    for error in errors:
                        messages.error(
                            request, f"{field.replace('_',' ').title()}: {error}"
                        )

        elif form_type == "email_change":
            email_form = UserEmailChangeForm(request.POST, instance=user)
            if email_form.is_valid():
                email_form.save()
                messages.success(request, "Email updated successfully.")
                return redirect("profile")
            else:
                for field, errors in email_form.errors.items():
                    for error in errors:
                        messages.error(
                            request, f"{field.replace('_',' ').title()}: {error}"
                        )
                if email_form.non_field_errors():
                    messages.error(request, email_form.non_field_errors().as_text())

        elif form_type == "password_change":
            password_form = PasswordChangeForm(user=user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Your password was successfully updated!")
                return redirect("profile")
            else:
                for field, errors in password_form.errors.items():
                    for error in errors:
                        field_name = (
                            field.replace("_", " ")
                            .replace("1", "")
                            .replace("2", "")
                            .title()
                        )
                        messages.error(request, f"{field_name}: {error}")
                if password_form.non_field_errors():
                    messages.error(request, password_form.non_field_errors().as_text())

        elif form_type == "delete_account":
            user_to_delete = request.user
            logout(request)
            user_to_delete.delete()
            messages.info(request, "Your account has been deleted.")
            return redirect("customers")

    context = {}
    return render(request, "customers/profile.html", context)


def cancel_reservation(request, reservation_id):
    reservation = get_object_or_404(
        Reservation, id=reservation_id, reserved_by=request.user
    )

    # Ensure the reservation can be canceled (not already completed or cancelled)
    if reservation.status in ["C", "X"]:
        messages.error(request, "This reservation cannot be cancelled.")
    else:
        # Update the reservation status to cancelled
        reservation.status = "X"

        # Store the cancellation reason if provided
        cancel_reason = request.POST.get("cancel_reason", "")

        customer_cancellation_message = (
            f"We have recieved your cancellation notice for reservation with "
            f"{reservation.barber.first_name.upper()} {reservation.barber.last_name.upper()} dated "
            f"{reservation.start_datetime.strftime('%B %d, %Y at %I:%M %p')}. "
            f'The reason you stated:\n"{cancel_reason}"\n\n'
            f"We will notify our team to update your reservation status."
        )

        barber_cancellation_message = (
            f"Kindly be informed that a customer has cancelled their reservation with you. The reservation with "
            f"{reservation.reserved_for_first_name.upper()} {reservation.reserved_for_last_name.upper()} dated "
            f"{reservation.start_datetime.strftime('%B %d, %Y at %I:%M %p')} has been cancelled. "
            f'The reason they stated:\n"{cancel_reason}"\n\n'
            f"We will notify our team to update your reservation status."
        )

        sms_sent_successfully = send_cancellation_sms(
            phone_number=reservation.reserved_for_phone,
            message_body=customer_cancellation_message,
            recipient_name=f"{reservation.reserved_for_first_name.upper()} {reservation.reserved_for_last_name.upper()}",
            sender_name="East K' Edge",
        )

        sms_sent_successfully = sms_sent_successfully and send_cancellation_sms(
            phone_number=reservation.barber.phone_number,
            message_body=barber_cancellation_message,
            recipient_name=f"{reservation.barber.first_name.upper()} {reservation.barber.last_name.upper()}",
            sender_name="East K' Edge",
        )

        if not sms_sent_successfully:
            print(f"SMS notification failed to send for reservation {reservation.id}")
        else:
            print("SMS notification successful")

        reservation.save()
        messages.success(request, "Reservation successfully cancelled.")

    return redirect("customer_reservations")


@login_required
@group_required("Customer")
def customer_reservations_view(request):
    reservations_qs = Reservation.objects.filter(reserved_by=request.user).order_by('-start_datetime')
    current_status_filter = request.GET.get('status_filter', '') # This will be "C", "X", "A,R", etc. from the form

    if current_status_filter:
        if current_status_filter == 'A,R': # Keep this as 'A,R' since it's the value from the select option
            reservations_qs = reservations_qs.filter(status__in=[
                Reservation.ReservationStatus.ACCEPTED,
                Reservation.ReservationStatus.REQUESTED
            ])
        # For single statuses, the current_status_filter will be 'C', 'X', or 'D'
        # These match the values of your ReservationStatus enum members
        elif current_status_filter in Reservation.ReservationStatus.values: # .values gives ['C', 'X', 'R', 'A', 'D']
            reservations_qs = reservations_qs.filter(status=current_status_filter)

    context = {
        'reservations': list(reservations_qs),
        'current_status_filter': current_status_filter,
    }
    return render(request, 'customers/customer-reservations.html', context)
