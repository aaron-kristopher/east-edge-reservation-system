from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.utils import timezone
from django.conf import settings

from datetime import timedelta, datetime
import json
import random
import string

# Your existing imports
from core.decorators import group_required
from barbers.models import Barber, Service
from .forms import UserProfileUpdateForm, UserEmailChangeForm, SignUpForm # Ensure SignUpForm is correct
from .models import UserModel # Your custom user model
from reservations.models import Reservation
from reservations.sms_utils import send_sms # IMPORT YOUR ACTUAL send_sms
# If send_cancellation_sms was specific, and send_sms is generic, use send_sms
# from reservations.sms_utils import send_cancellation_sms # You might not need this specific one here

# For OTP generation and storage (using session here for simplicity)
OTP_SESSION_KEY_PREFIX = 'password_reset_otp_'
OTP_EXPIRY_MINUTES = 5 # OTP valid for 5 minutes
OTP_ATTEMPTS_SESSION_KEY_PREFIX = 'password_reset_otp_attempts_'
MAX_OTP_ATTEMPTS = 3

# --- Helper function to generate OTP ---
def generate_otp(length=4): # Changed default to 4 to match HTML
    return ''.join(random.choices(string.digits, k=length))

# --- Your Existing Views ---
def customers(request):
    context = {"services": Service.objects.all(), "barbers": Barber.objects.all()}
    return render(request, "customers/index.html", context)

def barbers(request): # This is an API-like view
    ids = request.GET.get("ids")
    if not ids:
        return JsonResponse([], safe=False) # Return empty if no ids
    try:
        ids_list = [int(i) for i in ids.split(",")]
        barbers_data = list(
            Barber.objects.annotate(
                matching_services=Count("services", filter=Q(services__id__in=ids_list))
            )
            .filter(matching_services=len(ids_list))
            .values('id', 'first_name', 'last_name', 'profile_picture', 'status') # Specify fields
        )
        # Handle profile_picture URL correctly
        for barber in barbers_data:
            if barber.get('profile_picture'): # Check if key exists and has a value
                try:
                    # This assumes profile_picture is an ImageField and .url works
                    # If it's just a path string, adjust accordingly
                    b_obj = Barber.objects.get(id=barber['id']) # Get actual object for ImageField
                    barber['profile_picture_url'] = b_obj.profile_picture.url if b_obj.profile_picture else None
                except Barber.DoesNotExist:
                    barber['profile_picture_url'] = None
            else:
                barber['profile_picture_url'] = None

        return JsonResponse(barbers_data, safe=False)
    except ValueError: # Handle case where ids are not integers
        return JsonResponse({'error': 'Invalid IDs provided'}, status=400)


def reservation_schedule(request): # Renders the page with the Flatpickr calendar
    # You might want to pass services and barbers here too if they are selected on this page
    context = {"services": Service.objects.all(), "barbers": Barber.objects.all()}
    return render(request, "customers/reservation_schedule.html", context)


def get_barber_reservations(request): # API for barber's existing reservations
    try:
        barber_id = int(request.GET.get("id"))
        date_str = request.GET.get("date") # Expecting YYYY-MM-DD
        # time_str = request.GET.get("time") # Expecting HH:MM AM/PM or HH:MM (24hr)

        if not date_str:
            return JsonResponse({'error': 'Date is required'}, status=400)

        # Convert date_str to datetime objects for start and end of the day
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        start_of_day = timezone.make_aware(datetime.combine(selected_date, datetime.min.time()))
        end_of_day = timezone.make_aware(datetime.combine(selected_date, datetime.max.time()))

        # Filter reservations for the given barber on the selected date
        # Consider only statuses that make a slot unavailable (e.g., Accepted, maybe Requested)
        reservations = list(
            Reservation.objects.filter(
                barber_id=barber_id,
                start_datetime__gte=start_of_day,
                start_datetime__lte=end_of_day,
                status__in=[Reservation.ReservationStatus.ACCEPTED, Reservation.ReservationStatus.REQUESTED]
            ).values('start_datetime', 'end_datetime') # Send only what's needed
        )
        return JsonResponse(reservations, safe=False)

    except ValueError:
        return JsonResponse({'error': 'Invalid barber ID or date format'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def customer_signup(request):
    # ... (Your existing signup logic - seems fine) ...
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            # ... (user creation and group assignment) ...
            user = form.save() # If SignUpForm is a ModelForm for UserModel
            from django.contrib.auth.models import Group
            try:
                customer_group = Group.objects.get(name="Customer")
                user.groups.add(customer_group)
            except Group.DoesNotExist:
                messages.error(request, "Customer group not found. Please contact admin.")
                # Decide if you want to proceed or stop user creation
            
            user.backend = "django.contrib.auth.backends.ModelBackend" # Or your custom EmailBackend
            login(request, user)
            return redirect("customers") # Or to a welcome page
        else:
            # Pass form with errors back to template
            return render(request, "accounts/signup.html", {"form": form})
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form})


def customer_login(request):
    # ... (Your existing login logic - seems fine) ...
    error_message = None
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, email=email, password=password) # Ensure your backend supports email auth
        if user is not None:
            login(request, user)
            if user.groups.filter(name="Receptionist").exists():
                return redirect("dashboard") # Receptionist dashboard
            else:
                next_url = request.POST.get("next") or request.GET.get("next")
                return redirect(next_url or "reservation") # Customer reservation or default
        else:
            error_message = "Invalid email or password."
    return render(request, "accounts/login.html", {"error": error_message})


def customer_logout(request):
    # ... (Your existing logout logic - seems fine) ...
    logout(request)
    messages.info(request, "You have been successfully logged out.")
    return redirect("customers")


@login_required
@group_required("Customer") # Ensure this decorator is correctly implemented
def reservation(request): # This is likely the main reservation creation page
    context = {"services": Service.objects.all(), "barbers": Barber.objects.all()}
    return render(request, "customers/reservation.html", context) # The HTML you provided last time

@login_required
def customers_profile(request):
    # ... (Your existing profile logic - seems fine) ...
    user = request.user
    if request.method == "POST":
        # ... your form handling ...
        pass # Placeholder for brevity
    profile_form = UserProfileUpdateForm(instance=user)
    email_form = UserEmailChangeForm(instance=user)
    password_form = PasswordChangeForm(user=user)
    context = {
        'profile_form': profile_form,
        'email_form': email_form,
        'password_form': password_form,
    }
    return render(request, "customers/profile.html", context)


@login_required
@group_required("Customer")
def customer_reservations_view(request): # View existing appointments
    # ... (Your existing logic for viewing appointments with filtering - seems fine) ...
    reservations_qs = Reservation.objects.filter(reserved_by=request.user).order_by('-start_datetime')
    current_status_filter = request.GET.get('status_filter', '')
    if current_status_filter:
        if current_status_filter == 'A,R':
            reservations_qs = reservations_qs.filter(status__in=[Reservation.ReservationStatus.ACCEPTED, Reservation.ReservationStatus.REQUESTED])
        elif current_status_filter in Reservation.ReservationStatus.values:
            reservations_qs = reservations_qs.filter(status=current_status_filter)
    context = {'reservations': list(reservations_qs), 'current_status_filter': current_status_filter}
    return render(request, 'customers/customer-reservations.html', context)


@login_required
def cancel_reservation(request, reservation_id): # Customer cancels their own reservation
    # ... (Your existing cancel_reservation logic - seems fine, ensure SMS utility is correct) ...
    # Make sure to use send_sms if send_cancellation_sms is not defined or is too specific
    reservation_obj = get_object_or_404(Reservation, id=reservation_id, reserved_by=request.user)
    if reservation_obj.status in [Reservation.ReservationStatus.COMPLETED, Reservation.ReservationStatus.CANCELLED]:
        messages.error(request, "This reservation cannot be cancelled.")
    else:
        reservation_obj.status = Reservation.ReservationStatus.CANCELLED
        cancel_reason = request.POST.get("cancel_reason", "Cancelled by customer.")
        # reservation_obj.cancellation_reason = cancel_reason # If you have a field
        reservation_obj.save()
        messages.success(request, "Reservation successfully cancelled.")
        # --- Send SMS to customer and barber ---
        company_name = getattr(settings, 'COMPANY_NAME', "East K' Edge")
        customer_name = reservation_obj.reserved_for_name()
        barber_name_upper = f"{reservation_obj.barber.first_name.upper()} {reservation_obj.barber.last_name.upper()}"
        reservation_dt_str = timezone.localtime(reservation_obj.start_datetime).strftime('%B %d, %Y at %I:%M %p')

        customer_msg = (
            f"Your cancellation notice for the reservation with {barber_name_upper} on {reservation_dt_str} "
            f"has been received. Reason: \"{cancel_reason}\"."
        )
        if reservation_obj.reserved_for_phone:
            send_sms(reservation_obj.reserved_for_phone, customer_msg, customer_name, company_name)

        barber_msg = (
            f"Customer {customer_name} has CANCELLED their reservation with you scheduled for "
            f"{reservation_dt_str}. Reason: \"{cancel_reason}\"."
        )
        if reservation_obj.barber.phone_number:
            send_sms(reservation_obj.barber.phone_number, barber_msg, reservation_obj.barber.first_name, company_name)

    return redirect("customer_reservations_view") # Or your 'My Appointments' URL name


# --- NEW VIEWS FOR FORGOT PASSWORD WITH SMS OTP ---

def send_password_reset_otp(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip()
            is_resend = data.get('resend', False) # Check if it's a resend request
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid request format.'}, status=400)

        if not email:
            return JsonResponse({'success': False, 'error': 'Email is required.'}, status=400)

        try:
            user = UserModel.objects.get(email=email)
        except UserModel.DoesNotExist:
            # Don't reveal if email exists for security, but log it.
            print(f"Password reset OTP attempt for non-existent email: {email}")
            # Still return a generic success to prevent email enumeration, but don't send SMS
            # For better UX, you might want to inform the user if the email isn't found,
            # but this is a security trade-off.
            # For this example, let's assume we inform:
            return JsonResponse({'success': False, 'error': 'No account found with that email address.'}, status=404)

        if not user.phone_number:
            return JsonResponse({'success': False, 'error': 'No phone number is associated with this account. Cannot send OTP.'}, status=400)

        otp_code = generate_otp()
        otp_expiry = timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)
        
        # Store OTP and expiry in session (you might prefer a DB table for more persistence)
        session_key_otp = f"{OTP_SESSION_KEY_PREFIX}{user.id}"
        session_key_expiry = f"{session_key_otp}_expiry"
        session_key_attempts = f"{OTP_ATTEMPTS_SESSION_KEY_PREFIX}{user.id}"

        request.session[session_key_otp] = otp_code
        request.session[session_key_expiry] = otp_expiry.isoformat() # Store as ISO string
        if is_resend or session_key_attempts not in request.session: # Reset attempts on first send or resend
            request.session[session_key_attempts] = MAX_OTP_ATTEMPTS

        # --- Send OTP via SMS ---
        company_name = getattr(settings, 'COMPANY_NAME', "East K' Edge")
        customer_name = user.first_name or "Customer"
        message_body = f"Your password reset OTP for {company_name} is: {otp_code}. It is valid for {OTP_EXPIRY_MINUTES} minutes."
        
        sms_sent = send_sms(
            phone_number=user.phone_number,
            message_body_content=message_body,
            recipient_name=customer_name, # Use user's name
            sender_name=company_name,
            use_formal_segmenter=False # Simple message, formal might be overkill
        )

        if sms_sent:
            print(f"Sent password reset OTP {otp_code} to {user.phone_number} for email {email}")
            return JsonResponse({'success': True, 'message': 'OTP sent to your registered phone number.'})
        else:
            # Log the failure, but don't necessarily tell the user the OTP for security.
            print(f"Failed to send password reset OTP to {user.phone_number} for email {email}")
            return JsonResponse({'success': False, 'error': 'Failed to send OTP. Please try again later.'}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)


def verify_password_reset_otp(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip()
            otp_entered = data.get('otp', '').strip()
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid request format.'}, status=400)

        if not email or not otp_entered:
            return JsonResponse({'success': False, 'error': 'Email and OTP are required.'}, status=400)

        try:
            user = UserModel.objects.get(email=email)
        except UserModel.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid request or user not found.'}, status=404) # Generic error

        session_key_otp = f"{OTP_SESSION_KEY_PREFIX}{user.id}"
        session_key_expiry = f"{session_key_otp}_expiry"
        session_key_attempts = f"{OTP_ATTEMPTS_SESSION_KEY_PREFIX}{user.id}"

        stored_otp = request.session.get(session_key_otp)
        expiry_str = request.session.get(session_key_expiry)
        attempts_left = request.session.get(session_key_attempts, 0)

        if attempts_left <= 0:
            # Clear OTP if attempts exhausted
            if session_key_otp in request.session: del request.session[session_key_otp]
            if session_key_expiry in request.session: del request.session[session_key_expiry]
            return JsonResponse({'success': False, 'error': 'No attempts left. Please request a new OTP.'}, status=410) # 410 Gone

        if not stored_otp or not expiry_str:
            request.session[session_key_attempts] = attempts_left - 1
            return JsonResponse({'success': False, 'error': 'OTP not found or expired. Please request a new one.'}, status=400)

        expiry_dt = datetime.fromisoformat(expiry_str)
        if timezone.now() > expiry_dt:
            # Clear expired OTP
            if session_key_otp in request.session: del request.session[session_key_otp]
            if session_key_expiry in request.session: del request.session[session_key_expiry]
            request.session[session_key_attempts] = attempts_left - 1
            return JsonResponse({'success': False, 'error': 'OTP has expired. Please request a new one.'}, status=400)

        if stored_otp == otp_entered:
            # OTP is correct, clear it and attempts from session to prevent reuse for password reset
            if session_key_otp in request.session: del request.session[session_key_otp]
            if session_key_expiry in request.session: del request.session[session_key_expiry]
            if session_key_attempts in request.session: del request.session[session_key_attempts] # Clear attempts too
            
            # Store a flag indicating OTP was verified for this user for a short period
            # This prevents someone from skipping OTP verification and going straight to reset password
            request.session[f'otp_verified_for_reset_{user.id}'] = True
            request.session.set_expiry(timedelta(minutes=OTP_EXPIRY_MINUTES + 2)) # Keep session alive a bit longer
            
            return JsonResponse({'success': True, 'message': 'OTP verified successfully.'})
        else:
            request.session[session_key_attempts] = attempts_left - 1
            return JsonResponse({'success': False, 'error': f'Invalid OTP. {attempts_left - 1} attempts remaining.'}, status=400)

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)


def reset_password_with_otp(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip()
            otp_provided_for_reset = data.get('otp', '').strip() # The OTP that was verified
            new_password = data.get('new_password')
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid request format.'}, status=400)

        if not email or not new_password or not otp_provided_for_reset:
            return JsonResponse({'success': False, 'error': 'Email, OTP, and new password are required.'}, status=400)
            
        try:
            user = UserModel.objects.get(email=email)
        except UserModel.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User not found.'}, status=404)

        # Check the OTP verification flag
        otp_verified_flag_key = f'otp_verified_for_reset_{user.id}'
        if not request.session.get(otp_verified_flag_key, False):
            return JsonResponse({'success': False, 'error': 'OTP not verified or verification expired. Please start over.'}, status=403)

        # At this point, OTP was verified by the previous step.
        # The `otp_provided_for_reset` could be re-checked against a one-time token if desired for extra security,
        # but the session flag is a reasonable approach here.

        # Validate password strength if needed here (e.g., length, complexity)
        if len(new_password) < 8: # Example: minimum length
             return JsonResponse({'success': False, 'error': 'Password must be at least 8 characters long.'}, status=400)

        user.set_password(new_password)
        user.save()

        # Clean up the OTP verification flag from session
        if otp_verified_flag_key in request.session:
            del request.session[otp_verified_flag_key]

        # Optional: Log the user in after password reset
        # user.backend = 'django.contrib.auth.backends.ModelBackend' # Or your custom
        # login(request, user)
        # messages.success(request, "Your password has been reset successfully and you are now logged in.")

        messages.success(request, "Your password has been reset successfully. Please log in.") # Message for redirect
        return JsonResponse({'success': True, 'message': 'Password reset successfully.'})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

def faq_page(request):
    """
    Renders the FAQ page.
    """
    # You could pass dynamic FAQ content from a database here if needed in the future
    # For now, all content is in the template.
    context = {}
    return render(request, 'customers/faq.html', context)
