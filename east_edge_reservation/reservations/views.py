# reservations/views.py

from django.http import JsonResponse
from django.views.decorators.http import require_POST

# from django.views.decorators.csrf import ensure_csrf_cookie # See previous note
from django.utils import timezone
import json
from datetime import datetime
from .models import Reservation
from barbers.models import Barber, Service
from django.contrib.auth.decorators import login_required

from .sms_utils import send_sms_via_traccar
import logging  # For logging errors in the view if needed

logger = logging.getLogger(__name__)  # For view-specific logging


@login_required
@require_POST
def create_reservation(request):
    try:
        data = json.loads(request.body)

        start_datetime_str = data.get("start_datetime")
        if not start_datetime_str:
            return JsonResponse({"error": "start_datetime is required"}, status=400)

        start_datetime = datetime.fromisoformat(start_datetime_str)
        if timezone.is_naive(start_datetime):
            start_datetime = timezone.make_aware(start_datetime)

        barber_id = data.get("barber_id")
        if not barber_id:
            return JsonResponse({"error": "barber_id is required"}, status=400)

        try:
            barber = Barber.objects.get(id=barber_id)
        except Barber.DoesNotExist:
            return JsonResponse({"error": "Barber not found"}, status=404)

        # Details for whom the reservation is made, primarily from request data
        is_reserved_for_self = data.get("is_reserved_for_self", False)

        # These will be used for the Reservation model AND for the SMS.
        # Assumes frontend always sends these, or they are None/empty if not applicable.
        sms_recipient_first_name = data.get("reserved_for_first_name")
        sms_recipient_last_name = data.get(
            "reserved_for_last_name"
        )  # Not used in SMS message currently, but good to have
        sms_recipient_phone = data.get("reserved_for_phone")

        # For populating the Reservation model accurately
        if is_reserved_for_self:
            # If for self, still use user's details for the model record,
            # but SMS can use the (potentially overriding) details from the request.
            model_reserved_for_first_name = request.user.first_name
            model_reserved_for_last_name = request.user.last_name
            model_reserved_for_email = request.user.email
            # If sms_recipient_phone from data is empty AND it's for self, try to get user's phone
            if not sms_recipient_phone:
                try:
                    # Replace with your actual logic to get the user's phone
                    sms_recipient_phone = request.user.customer_profile.phone_number
                except AttributeError:
                    logger.warning(
                        f"Could not retrieve phone number from user profile for self-reservation by {request.user.username}"
                    )
                    # sms_recipient_phone will remain None or empty if not provided in data and not on profile
            model_reserved_for_phone = (
                sms_recipient_phone  # Use the determined phone for the model
            )
        else:
            # If not for self, model details are same as SMS recipient details from request data
            model_reserved_for_first_name = sms_recipient_first_name
            model_reserved_for_last_name = sms_recipient_last_name
            model_reserved_for_email = data.get("reserved_for_email")
            model_reserved_for_phone = sms_recipient_phone

        # Basic validation for essential details if sending SMS
        if not sms_recipient_first_name or not sms_recipient_phone:
            logger.warning(
                "Reservation created, but first name or phone for SMS recipient is missing from request data. SMS not sent."
            )
            # Decide if this should be an error or just a warning.
            # For now, we'll proceed with reservation creation but skip SMS.

        reservation = Reservation(
            start_datetime=start_datetime,
            barber=barber,
            reserved_by=request.user,
            is_reserved_for_self=is_reserved_for_self,
            reserved_for_first_name=model_reserved_for_first_name,
            reserved_for_last_name=model_reserved_for_last_name,
            reserved_for_email=model_reserved_for_email,
            reserved_for_phone=model_reserved_for_phone,  # Storing the determined phone on the model
        )
        reservation.save()

        service_ids = data.get("services", [])
        if not service_ids:
            reservation.delete()  # Rollback: delete reservation if no services
            return JsonResponse(
                {"error": "At least one service must be selected"}, status=400
            )

        services = Service.objects.filter(id__in=service_ids)
        reservation.services.set(services)

        reservation.end_datetime = reservation.calculate_end_datetime()
        reservation.save(update_fields=["end_datetime"])

        # --- Send SMS Notification ---
        if (
            sms_recipient_phone and sms_recipient_first_name
        ):  # Check again, ensure we have necessary info for SMS
            service_names = ", ".join([s.name for s in reservation.services.all()])
            sms_message = (
                f"Hi {sms_recipient_first_name}, your reservation #{reservation.id} at East Edge "
                f"with {barber.name} for {service_names} on "
                f"{reservation.start_datetime.strftime('%b %d, %Y at %I:%M %p')} is booked and pending confirmation. "
            )

            sms_sent_successfully = send_sms_via_traccar(
                sms_recipient_phone, sms_message
            )

            if not sms_sent_successfully:
                logger.warning(
                    f"SMS notification failed to send for reservation {reservation.id} to {sms_recipient_phone}"
                )
        else:
            logger.info(
                f"Skipping SMS for reservation {reservation.id}: phone number or first name for SMS recipient not provided/found."
            )
        # --- End SMS Notification ---

        return JsonResponse(
            {
                "id": reservation.id,
                "message": "Reservation created successfully.",  # Simpler message, frontend can infer SMS status if needed
                "start_datetime": reservation.start_datetime.isoformat(),
                "end_datetime": (
                    reservation.end_datetime.isoformat()
                    if reservation.end_datetime
                    else None
                ),
            }
        )

    except KeyError as e:
        logger.error(f"Missing key in request data for create_reservation: {str(e)}")
        return JsonResponse({"error": f"Missing required field: {str(e)}"}, status=400)
    except Barber.DoesNotExist:
        return JsonResponse({"error": "Selected barber not found."}, status=404)
    except Service.DoesNotExist:
        return JsonResponse(
            {"error": "One or more selected services not found."}, status=404
        )
    except Exception:
        logger.exception(
            f"Unexpected error creating reservation for user {request.user.username}"
        )  # Logs full traceback
        return JsonResponse(
            {"error": "An unexpected error occurred. Please try again."}, status=500
        )
