from datetime import datetime, timedelta, time
from django.http import JsonResponse
from django.views import View
from django.utils import timezone
from django.utils.dateparse import parse_date
from .models import Service, Barber
from reservations.models import Reservation
from django.shortcuts import render
from core.decorators import group_required

from datetime import timezone as dt_timezone
import logging

from .models import Schedule

logger = logging.getLogger(__name__)


class AvailableTimeSlotsView(View):
    def get(self, request):
        barber_id = request.GET.get("barber_id")
        date_str = request.GET.get("date")
        service_ids = request.GET.getlist("service_ids[]")

        if not barber_id or not date_str or not service_ids:
            return JsonResponse({"error": "Missing parameters"}, status=400)

        try:
            barber = Barber.objects.get(pk=barber_id)
            target_date = parse_date(date_str)
            if not target_date:
                raise ValueError("Invalid date format. Please use YYYY-MM-DD.")

            services = Service.objects.filter(id__in=service_ids)
            if not services.exists():
                logger.warning(
                    f"No valid services found for service_ids: {service_ids}"
                )
                return JsonResponse(
                    {"available_slots": [], "message": "No valid services selected."}
                )

            total_duration_minutes = sum([s.estimated_time for s in services])
            if total_duration_minutes <= 0:
                logger.warning(
                    f"Total service duration is zero or negative for service_ids: {service_ids}"
                )
                return JsonResponse(
                    {
                        "available_slots": [],
                        "message": "Total service duration must be positive.",
                    }
                )
            total_duration_delta = timedelta(minutes=total_duration_minutes)

        except Barber.DoesNotExist:
            return JsonResponse({"error": "Barber not found."}, status=404)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            logger.error(
                f"Error fetching initial data for available slots: {e}", exc_info=True
            )
            return JsonResponse(
                {"error": "An unexpected error occurred processing your request."},
                status=500,
            )

        all_available_slots_for_day = []
        slot_interval = timedelta(minutes=30)

        local_tz = timezone.get_current_timezone()

        shop_opens_time_local_def = time(8, 0)
        shop_closes_time_local_def = time(17, 30)

        shop_opens_on_date_local = datetime.combine(
            target_date, shop_opens_time_local_def, tzinfo=local_tz
        )
        shop_closes_on_date_local = datetime.combine(
            target_date, shop_closes_time_local_def, tzinfo=local_tz
        )
        logger.debug(
            f"Shop operating (local TZ {local_tz}): {shop_opens_on_date_local.strftime('%Y-%m-%d %H:%M %Z%z')} to {shop_closes_on_date_local.strftime('%Y-%m-%d %H:%M %Z%z')}"
        )

        day_start_local = datetime.combine(target_date, time.min, tzinfo=local_tz)
        day_end_local = datetime.combine(target_date, time.max, tzinfo=local_tz)

        # --- CORRECTED UTC CONVERSION ---
        day_start_utc = day_start_local.astimezone(
            dt_timezone.utc
        )  # Use datetime.timezone.utc
        day_end_utc = day_end_local.astimezone(
            dt_timezone.utc
        )  # Use datetime.timezone.utc
        # --- END CORRECTION ---
        logger.debug(
            f"Target local day ({target_date}) in UTC: {day_start_utc} to {day_end_utc}"
        )

        barber_schedules_on_date_utc = Schedule.objects.filter(
            barber=barber,
            start_datetime__lt=day_end_utc,
            end_datetime__gt=day_start_utc,
        ).order_by("start_datetime")

        if not barber_schedules_on_date_utc.exists():
            return JsonResponse(
                {
                    "available_slots": [],
                    "message": "Barber is not scheduled to work on this date.",
                }
            )

        accepted_reservations_utc = Reservation.objects.filter(
            barber=barber,
            start_datetime__gte=day_start_utc,
            start_datetime__lt=day_end_utc,
            status=Reservation.ReservationStatus.ACCEPTED,
        )
        logger.debug(
            f"Barber {barber_id} on local date {target_date}: Found {accepted_reservations_utc.count()} accepted reservations (queried in UTC)."
        )

        for duty_period_utc in barber_schedules_on_date_utc:
            # When converting from UTC (or any aware datetime) to another timezone (local_tz)
            # or from local_tz to UTC, .astimezone() is correct.
            duty_start_actual_local = duty_period_utc.start_datetime.astimezone(
                local_tz
            )
            duty_end_actual_local = duty_period_utc.end_datetime.astimezone(local_tz)

            logger.debug(
                f"Raw duty period (UTC from DB): {duty_period_utc.start_datetime} to {duty_period_utc.end_datetime}"
            )
            logger.debug(
                f"Duty Period (Converted to Local {local_tz}): {duty_start_actual_local.strftime('%Y-%m-%d %H:%M:%S %Z%z')} to {duty_end_actual_local.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"
            )

            duty_start_clamped_to_local_date = max(
                duty_start_actual_local, day_start_local
            )
            duty_end_clamped_to_local_date = min(duty_end_actual_local, day_end_local)
            logger.debug(
                f"Duty Period Clamped to Local Date ({local_tz}): {duty_start_clamped_to_local_date.strftime('%Y-%m-%d %H:%M:%S %Z%z')} to {duty_end_clamped_to_local_date.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"
            )

            operational_start_for_period = max(
                duty_start_clamped_to_local_date, shop_opens_on_date_local
            )
            operational_end_for_period = min(
                duty_end_clamped_to_local_date, shop_closes_on_date_local
            )

            logger.debug(
                f"Operational Window ({local_tz}): {operational_start_for_period.strftime('%Y-%m-%d %H:%M:%S %Z%z')} to {operational_end_for_period.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"
            )

            if operational_start_for_period >= operational_end_for_period:
                logger.debug(
                    "  Skipping duty period as it falls outside combined shop/duty hours."
                )
                continue

            current_potential_slot_start = operational_start_for_period

            while (
                current_potential_slot_start + total_duration_delta
                <= operational_end_for_period
            ):
                current_potential_slot_end = (
                    current_potential_slot_start + total_duration_delta
                )
                is_slot_available = True

                for res_utc in accepted_reservations_utc:
                    res_start_local = res_utc.start_datetime.astimezone(local_tz)

                    if res_utc.end_datetime:
                        res_end_local = res_utc.end_datetime.astimezone(local_tz)
                    else:
                        res_services_duration_minutes = 0
                        try:
                            res_services_duration_minutes = sum(
                                [s.estimated_time for s in res_utc.services.all()]
                            )
                        except Exception as service_sum_ex:
                            logger.error(
                                f"Could not sum service durations for reservation {res_utc.id}: {service_sum_ex}"
                            )

                        res_end_local = res_start_local + timedelta(
                            minutes=(
                                res_services_duration_minutes
                                if res_services_duration_minutes > 0
                                else 30
                            )
                        )

                    if not (
                        current_potential_slot_end <= res_start_local
                        or current_potential_slot_start >= res_end_local
                    ):
                        is_slot_available = False
                        logger.debug(
                            f"  Conflict: Slot {current_potential_slot_start.strftime('%H:%M')}-{current_potential_slot_end.strftime('%H:%M')} overlaps with reservation {res_start_local.strftime('%H:%M')}-{res_end_local.strftime('%H:%M')} (local times)"
                        )
                        break

                if is_slot_available:
                    slot_str = current_potential_slot_start.strftime("%I:%M %p")
                    if slot_str not in all_available_slots_for_day:
                        all_available_slots_for_day.append(slot_str)
                        logger.debug(f"  Added available slot: {slot_str}")

                current_potential_slot_start += slot_interval

        if all_available_slots_for_day:
            try:
                sorted_slots = sorted(
                    all_available_slots_for_day,
                    key=lambda x: datetime.strptime(x, "%I:%M %p").time(),
                )
                all_available_slots_for_day = sorted_slots
            except ValueError:
                logger.error(
                    "Error sorting time slots. Proceeding with unsorted.", exc_info=True
                )

        return JsonResponse({"available_slots": all_available_slots_for_day})


@group_required("Barber")
def schedule(request):
    return render(request, "barbers/reservations.html")
