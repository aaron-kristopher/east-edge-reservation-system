from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.utils import timezone
import json
from datetime import datetime
from .models import Reservation
from barbers.models import Barber, Service
from django.contrib.auth.decorators import login_required

@login_required
@require_POST
@ensure_csrf_cookie
def create_reservation(request):
    try:
        data = json.loads(request.body)
        
        start_datetime = datetime.fromisoformat(data['start_datetime'])
        if timezone.is_naive(start_datetime):
            start_datetime = timezone.make_aware(start_datetime)
        
        try:
            barber = Barber.objects.get(id=data['barber_id'])
        except Barber.DoesNotExist:
            return JsonResponse({'error': 'Barber not found'}, status=404)
        
        reservation = Reservation(
            start_datetime=start_datetime,
            barber=barber,
            reserved_by=request.user,
            is_reserved_for_self=data['is_reserved_for_self'],
            reserved_for_first_name=data['reserved_for_first_name'],
            reserved_for_last_name=data['reserved_for_last_name'],
            reserved_for_email=data['reserved_for_email'],
            reserved_for_phone=data['reserved_for_phone'],
        )
        reservation.save()
        
        service_ids = data['services']
        services = Service.objects.filter(id__in=service_ids)
        reservation.services.set(services)
        
        reservation.end_datetime = reservation.calculate_end_datetime()
        reservation.save()
        
        return JsonResponse({
            'id': reservation.id,
            'message': 'Reservation created successfully',
            'start_datetime': reservation.start_datetime.isoformat(),
            'end_datetime': reservation.end_datetime.isoformat() if reservation.end_datetime else None,
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)