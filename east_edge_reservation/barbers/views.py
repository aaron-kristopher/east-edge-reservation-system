from datetime import datetime, timedelta, time
from django.http import JsonResponse
from django.views import View
from django.utils import timezone
from django.utils.dateparse import parse_date
from .models import Service, Barber
from reservations.models import Reservation
from django.shortcuts import render
from core.decorators import group_required


# def barbers(request):
#     barbers = Barber.objects.all()
#     context = {"barbers": barbers}
#     return render(request, "barbers/index.html", context)


# def services(request):
#     services = Service.objects.all()
#     context = {"services": services}
#     return render(request, "services/index.html", context)


class AvailableTimeSlotsView(View):
    def get(self, request):
        barber_id = request.GET.get("barber_id")
        date_str = request.GET.get("date")
        service_ids = request.GET.getlist("service_ids[]")
        
        if not barber_id or not date_str or not service_ids:
            return JsonResponse({"error": "Missing parameters."}, status=400)

        try:
            barber = Barber.objects.get(pk=barber_id)
            date = parse_date(date_str)
            services = Service.objects.filter(id__in=service_ids)
            total_duration = sum([s.estimated_time for s in services])  # minutes
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

        # Define working hours
        print(total_duration)
        start_time = time(8, 0)
        end_time = time(17, 30)
        slot_interval = timedelta(minutes=30)
        all_slots = []

        current_start = timezone.make_aware(datetime.combine(date, start_time))
        end_of_day = timezone.make_aware(datetime.combine(date, end_time))

        # Get reservations for this barber on that day
        existing_reservations = Reservation.objects.filter(
            barber=barber, start_datetime__date=date
        )

        while current_start + timedelta(minutes=total_duration) <= end_of_day:
            current_end = current_start + timedelta(minutes=total_duration)
            conflict = False

            for res in existing_reservations:
                res_start = res.start_datetime
                res_end = res.end_datetime or (
                    res_start + timedelta(minutes=30)
                )  # fallback if end not set

                # Check for overlap
                if not (current_end <= res_start or current_start >= res_end):
                    conflict = True
                    break

            if not conflict:
                all_slots.append(current_start.strftime("%I:%M %p"))

            current_start += slot_interval

        return JsonResponse({"available_slots": all_slots})
    
@group_required('Barber')
def schedule(request):
    return render(request, "barbers/reservations.html")


