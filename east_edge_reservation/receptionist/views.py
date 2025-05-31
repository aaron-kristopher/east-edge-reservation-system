from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings # For settings.USE_TZ and COMPANY_NAME
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt # Use with caution, especially for GET APIs
from datetime import datetime, timedelta, time as dt_time # Make sure time is imported

from core.decorators import group_required # Your custom decorator
from barbers.models import Barber, Service, Schedule # Ensure Schedule is imported
from reservations.models import Reservation # Your Reservation model
from customers.models import UserModel
from reservations.sms_utils import send_sms # Your SMS sending utility

# --- Main Receptionist Dashboard View (Handles GET and various POST form_types) ---
@group_required("Receptionist")
def receptionist(request):
    # --- POST Request Handling ---
    if request.method == "POST" and "form_type" in request.POST:
        form_type = request.POST.get("form_type")

        # --- Edit Reservation ---
        if form_type == "edit_reservation":
            reservation_id = request.POST.get("reservation_id")
            try:
                reservation = Reservation.objects.select_related('barber', 'reserved_by').get(id=reservation_id)
                original_status = reservation.status

                barber_id = request.POST.get("barber_id")
                if barber_id: reservation.barber_id = barber_id

                reserved_by_id = request.POST.get("reserved_by_id")
                if reserved_by_id: reservation.reserved_by_id = reserved_by_id

                reservation.reserved_for_first_name = request.POST.get("reserved_for_first_name", reservation.reserved_for_first_name)
                reservation.reserved_for_last_name = request.POST.get("reserved_for_last_name", reservation.reserved_for_last_name)
                reservation.reserved_for_email = request.POST.get("reserved_for_email", reservation.reserved_for_email)
                reservation.reserved_for_phone = request.POST.get("reserved_for_phone", reservation.reserved_for_phone)
                reservation.is_reserved_for_self = "is_reserved_for_self" in request.POST

                date_str = request.POST.get("date")
                time_str = request.POST.get("time")
                if date_str and time_str:
                    naive_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                    if settings.USE_TZ:
                        reservation.start_datetime = timezone.make_aware(naive_dt, timezone.get_default_timezone())
                    else:
                        reservation.start_datetime = naive_dt
                
                new_status = request.POST.get("status")
                status_changed = False
                if new_status and new_status != original_status:
                    reservation.status = new_status
                    status_changed = True

                reservation.save() 

                if 'services' in request.POST:
                    service_ids = request.POST.getlist("services")
                    reservation.services.set(service_ids)

                messages.success(request, "Reservation updated successfully.")

                if status_changed:
                    customer_phone = reservation.reserved_for_phone
                    customer_name = reservation.reserved_for_name()
                    barber_name_formatted = f"{reservation.barber.first_name.upper()} {reservation.barber.last_name.upper()}"
                    reservation_datetime_formatted = timezone.localtime(reservation.start_datetime).strftime('%B %d, %Y at %I:%M %p')
                    company_name = getattr(settings, 'COMPANY_NAME', "East K' Edge")
                    sms_message_body = ""
                    send_notification_flag = True

                    if new_status == Reservation.ReservationStatus.ACCEPTED:
                        sms_message_body = (
                            f"Your reservation at {company_name} with {barber_name_formatted} "
                            f"on {reservation_datetime_formatted} has been ACCEPTED. We look forward to seeing you!"
                        )
                    elif new_status == Reservation.ReservationStatus.DECLINED:
                        sms_message_body = (
                            f"We regret to inform you that your reservation at {company_name} "
                            f"with {barber_name_formatted} on {reservation_datetime_formatted} has been DECLINED. "
                            f"Please contact us if you have any questions."
                        )
                    elif new_status == Reservation.ReservationStatus.COMPLETED:
                        sms_message_body = (
                            f"Thank you for choosing {company_name}! Your appointment with "
                            f"{barber_name_formatted} on {reservation_datetime_formatted} is now marked as COMPLETED. "
                            f"We hope you enjoyed your service!"
                        )
                    elif new_status == Reservation.ReservationStatus.CANCELLED:
                        sms_message_body = (
                            f"Your reservation at {company_name} with {barber_name_formatted} "
                            f"on {reservation_datetime_formatted} has been CANCELLED by the salon. "
                            f"Please contact us for more details."
                        )
                    else:
                        send_notification_flag = False

                    if send_notification_flag and customer_phone and sms_message_body:
                        sms_sent = send_sms(
                            phone_number=customer_phone,
                            message_body_content=sms_message_body,
                            recipient_name=customer_name,
                            sender_name=company_name,
                            use_formal_segmenter=True
                        )
                        if sms_sent: messages.info(request, "SMS notification sent to customer.")
                        else: messages.warning(request, "Failed to send SMS notification to customer.")
                
                return redirect("dashboard")
            except Reservation.DoesNotExist: messages.error(request, "Reservation not found.")
            except Exception as e:
                messages.error(request, f"Error updating reservation: {str(e)}")
            return redirect("dashboard")

        # --- Quick Status Update (Accept/Decline from table buttons) ---
        elif form_type == "quick_update_status":
            reservation_id = request.POST.get("reservation_id")
            new_status_code = request.POST.get("new_status") 
            decline_reason = request.POST.get("decline_reason", "")
            try:
                reservation = Reservation.objects.select_related('barber', 'reserved_by').get(id=reservation_id)
                original_status = reservation.status
                if original_status == Reservation.ReservationStatus.REQUESTED and \
                   new_status_code in [Reservation.ReservationStatus.ACCEPTED, Reservation.ReservationStatus.DECLINED]:
                    reservation.status = new_status_code
                    reservation.save()
                    action_taken_display = "ACCEPTED" if new_status_code == Reservation.ReservationStatus.ACCEPTED else "DECLINED"
                    messages.success(request, f"Reservation for {reservation.reserved_for_name()} has been {action_taken_display}.")
                    customer_phone = reservation.reserved_for_phone
                    customer_name = reservation.reserved_for_name()
                    barber_name_formatted = f"{reservation.barber.first_name.upper()} {reservation.barber.last_name.upper()}"
                    reservation_datetime_formatted = timezone.localtime(reservation.start_datetime).strftime('%B %d, %Y at %I:%M %p')
                    company_name = getattr(settings, 'COMPANY_NAME', "East K' Edge")
                    sms_message_body = ""
                    if new_status_code == Reservation.ReservationStatus.ACCEPTED:
                        sms_message_body = (
                            f"Great news! Your reservation at {company_name} with {barber_name_formatted} "
                            f"on {reservation_datetime_formatted} has been ACCEPTED. We look forward to seeing you."
                        )
                    elif new_status_code == Reservation.ReservationStatus.DECLINED:
                        reason_text = f" Reason: {decline_reason}." if decline_reason.strip() else ""
                        sms_message_body = (
                            f"We regret to inform you that your reservation at {company_name} "
                            f"with {barber_name_formatted} on {reservation_datetime_formatted} has been DECLINED.{reason_text} "
                            f"Please contact us if you have any questions."
                        )
                    if customer_phone and sms_message_body:
                        sms_sent = send_sms(
                            phone_number=customer_phone,
                            message_body_content=sms_message_body,
                            recipient_name=customer_name,
                            sender_name=company_name,
                            use_formal_segmenter=True
                        )
                        if sms_sent: messages.info(request, f"SMS for {action_taken_display.lower()} status sent.")
                        else: messages.warning(request, f"Failed to send SMS for {action_taken_display.lower()} status.")
                elif original_status != Reservation.ReservationStatus.REQUESTED:
                    messages.warning(request, "This reservation is not in 'Requested' state.")
                else:
                    messages.error(request, "Invalid status update for quick action.")
            except Reservation.DoesNotExist: messages.error(request, "Reservation not found.")
            except Exception as e:
                messages.error(request, f"Error updating status: {str(e)}")
            return redirect("dashboard")

        # --- Admin Cancels Reservation (from dedicated Cancel Modal) ---
        elif form_type == "cancel_reservation_admin":
            reservation_id = request.POST.get("reservation_id_to_cancel")
            admin_cancel_reason = request.POST.get("cancel_reason", "Cancelled by staff.")
            try:
                reservation = Reservation.objects.select_related('barber', 'reserved_by').get(id=reservation_id)
                if reservation.status not in [Reservation.ReservationStatus.COMPLETED, Reservation.ReservationStatus.CANCELLED]:
                    original_status = reservation.status
                    reservation.status = Reservation.ReservationStatus.CANCELLED
                    reservation.save()
                    messages.success(request, f"Reservation for {reservation.reserved_for_name()} cancelled by admin.")
                    if original_status != Reservation.ReservationStatus.CANCELLED:
                        customer_phone = reservation.reserved_for_phone
                        customer_name = reservation.reserved_for_name()
                        barber_name_formatted = f"{reservation.barber.first_name.upper()} {reservation.barber.last_name.upper()}"
                        reservation_datetime_formatted = timezone.localtime(reservation.start_datetime).strftime('%B %d, %Y at %I:%M %p')
                        company_name = getattr(settings, 'COMPANY_NAME', "East K' Edge")
                        sms_message_body = (
                            f"Your reservation at {company_name} with {barber_name_formatted} "
                            f"on {reservation_datetime_formatted} has been CANCELLED by the salon. "
                            f"Reason: {admin_cancel_reason}. Please contact us for further assistance."
                        )
                        if customer_phone and sms_message_body:
                            sms_sent = send_sms(
                                phone_number=customer_phone,
                                message_body_content=sms_message_body,
                                recipient_name=customer_name,
                                sender_name=company_name,
                                use_formal_segmenter=True
                            )
                            if sms_sent: messages.info(request, "Cancellation SMS sent to customer.")
                            else: messages.warning(request, "Failed to send cancellation SMS.")
                else:
                    messages.warning(request, "This reservation cannot be cancelled.")
            except Reservation.DoesNotExist: messages.error(request, "Reservation not found.")
            except Exception as e:
                messages.error(request, f"Error cancelling reservation: {str(e)}")
            return redirect("dashboard")

        # --- Add Barber ---
        elif form_type == 'add_barber':
            try:
                barber = Barber()
                barber.first_name = request.POST.get('first_name', '')
                barber.last_name = request.POST.get('last_name', '')
                barber.phone_number = request.POST.get('phone_number', '')
                barber.status = request.POST.get('status', Barber.BarberStatus.AVAILABLE)
                if 'profile_picture' in request.FILES:
                    barber.profile_picture = request.FILES['profile_picture']
                barber.save() 
                service_ids = request.POST.getlist('services')
                if service_ids: barber.services.set(service_ids)
                messages.success(request, 'Barber added successfully.')
            except Exception as e: messages.error(request, f'Error adding barber: {str(e)}')
            return redirect("dashboard")

        # --- Edit Barber ---
        elif form_type == 'edit_barber':
            barber_id = request.POST.get('barber_id')
            try:
                barber = Barber.objects.get(id=barber_id)
                barber.first_name = request.POST.get('first_name', barber.first_name)
                barber.last_name = request.POST.get('last_name', barber.last_name)
                barber.phone_number = request.POST.get('phone_number', barber.phone_number)
                barber.status = request.POST.get('status', barber.status)
                if 'remove_profile_picture' in request.POST: barber.profile_picture = None
                elif 'profile_picture' in request.FILES: barber.profile_picture = request.FILES['profile_picture']
                barber.save()
                if 'services' in request.POST:
                    service_ids = request.POST.getlist('services')
                    barber.services.set(service_ids)
                messages.success(request, 'Barber updated successfully.')
            except Barber.DoesNotExist: messages.error(request, 'Barber not found.')
            except Exception as e: messages.error(request, f'Error updating barber: {str(e)}')
            return redirect("dashboard")

        # --- Delete Barber (Single) ---
        elif form_type == 'delete_barber':
            barber_id = request.POST.get('barber_id')
            try:
                Barber.objects.filter(id=barber_id).delete()
                messages.success(request, 'Barber deleted successfully.')
            except Exception as e: messages.error(request, f'Error deleting barber: {str(e)}')
            return redirect("dashboard")
            
        # --- Delete Barbers (Multiple) ---
        elif form_type == 'delete_barbers':
            barber_ids = request.POST.getlist('selected_barbers')
            if barber_ids:
                deleted_count, _ = Barber.objects.filter(id__in=barber_ids).delete()
                messages.success(request, f'{deleted_count} barber(s) deleted successfully.')
            else: messages.warning(request, 'No barbers selected for deletion.')
            return redirect("dashboard")

        # --- Add Service ---
        elif form_type == 'add_service':
            try:
                Service.objects.create(
                    service_name=request.POST.get('service_name', ''),
                    price=float(request.POST.get('price', 0)),
                    estimated_time=int(request.POST.get('estimated_time', 0)),
                    category=request.POST.get('category', Service.ServiceCategory.HAIR)
                )
                messages.success(request, 'Service added successfully.')
            except Exception as e: messages.error(request, f'Error adding service: {str(e)}')
            return redirect("dashboard")

        # --- Edit Service ---
        elif form_type == 'edit_service':
            service_id = request.POST.get('service_id')
            try:
                service = Service.objects.get(id=service_id)
                service.service_name = request.POST.get('service_name', service.service_name)
                service.price = float(request.POST.get('price', service.price))
                service.estimated_time = int(request.POST.get('estimated_time', service.estimated_time))
                service.category = request.POST.get('category', service.category)
                service.save()
                messages.success(request, 'Service updated successfully.')
            except Service.DoesNotExist: messages.error(request, 'Service not found.')
            except Exception as e: messages.error(request, f'Error updating service: {str(e)}')
            return redirect("dashboard")

        # --- Delete Service (Single) ---
        elif form_type == 'delete_service':
            service_id = request.POST.get('service_id')
            try:
                Service.objects.filter(id=service_id).delete()
                messages.success(request, 'Service deleted successfully.')
            except Exception as e: messages.error(request, f'Error deleting service: {str(e)}')
            return redirect("dashboard")
        
        # --- Delete Reservations (Multiple) ---
        elif form_type == 'delete_reservations':
            reservation_ids = request.POST.getlist('reservation_ids')
            if reservation_ids:
                deleted_count, _ = Reservation.objects.filter(id__in=reservation_ids).delete()
                messages.success(request, f'{deleted_count} reservation(s) deleted successfully.')
            else:
                messages.warning(request, 'No reservations selected for deletion.')
            return redirect("dashboard")

        # --- Generate Schedules ---
        elif form_type == "generate_schedules":
            barber_ids = request.POST.getlist("barber_ids")
            if not barber_ids:
                messages.warning(request, "No barbers selected for schedule generation.")
                return redirect("dashboard")
            try:
                barbers_to_schedule = Barber.objects.filter(id__in=barber_ids)
                today = timezone.now().date()
                next_sunday = today + timedelta(days=(6 - today.weekday()) % 7)
                schedules_to_create = []
                for barber in barbers_to_schedule:
                    for i in range(7):  # Sunday to Saturday
                        schedule_date = next_sunday + timedelta(days=i)
                        # Naive datetime for start and end
                        start_naive = datetime.combine(schedule_date, dt_time(8, 0, 0)) # 8:00 AM
                        end_naive = datetime.combine(schedule_date, dt_time(17, 30, 0)) # 5:30 PM
                        
                        if settings.USE_TZ:
                            start_aware = timezone.make_aware(start_naive, timezone.get_default_timezone())
                            end_aware = timezone.make_aware(end_naive, timezone.get_default_timezone())
                        else:
                            start_aware = start_naive
                            end_aware = end_naive
                        
                        schedules_to_create.append(
                            Schedule(barber=barber, start_datetime=start_aware, end_datetime=end_aware)
                        )
                Schedule.objects.bulk_create(schedules_to_create)
                messages.success(request, f"Schedules created for {len(barbers_to_schedule)} barbers from {next_sunday} to {next_sunday + timedelta(days=6)}.")
            except Exception as e:
                messages.error(request, f"Error generating schedules: {str(e)}")
            return redirect("dashboard")

        # --- Edit Schedule ---
        elif form_type == "edit_schedule":
            schedule_id = request.POST.get("schedule_id")
            try:
                schedule = Schedule.objects.get(id=schedule_id)
                
                barber_id = request.POST.get("barber_id")
                if barber_id: schedule.barber_id = barber_id

                start_date_str = request.POST.get("start_date")
                start_time_str = request.POST.get("start_time")
                end_date_str = request.POST.get("end_date")
                end_time_str = request.POST.get("end_time")

                if start_date_str and start_time_str:
                    start_naive_dt = datetime.strptime(f"{start_date_str} {start_time_str}", "%Y-%m-%d %H:%M")
                    if settings.USE_TZ:
                        schedule.start_datetime = timezone.make_aware(start_naive_dt, timezone.get_default_timezone())
                    else:
                        schedule.start_datetime = start_naive_dt
                
                if end_date_str and end_time_str:
                    end_naive_dt = datetime.strptime(f"{end_date_str} {end_time_str}", "%Y-%m-%d %H:%M")
                    if settings.USE_TZ:
                        schedule.end_datetime = timezone.make_aware(end_naive_dt, timezone.get_default_timezone())
                    else:
                        schedule.end_datetime = end_naive_dt
                
                schedule.save()
                messages.success(request, "Schedule updated successfully.")
            except Schedule.DoesNotExist:
                messages.error(request, "Schedule not found.")
            except Exception as e:
                messages.error(request, f"Error updating schedule: {str(e)}")
            return redirect("dashboard")

        # --- Delete Single Schedule ---
        elif form_type == "delete_schedule":
            schedule_id = request.POST.get("schedule_id")
            try:
                schedule_instance = Schedule.objects.get(id=schedule_id)
                barber_name = f"{schedule_instance.barber.first_name} {schedule_instance.barber.last_name}"
                date_str = timezone.localtime(schedule_instance.start_datetime).strftime('%Y-%m-%d')
                schedule_instance.delete()
                messages.success(request, f"Schedule for {barber_name} on {date_str} deleted successfully.")
            except Schedule.DoesNotExist:
                messages.error(request, "Schedule not found.")
            except Exception as e:
                messages.error(request, f"Error deleting schedule: {str(e)}")
            return redirect("dashboard")

        # --- Delete Selected Schedules ---
        elif form_type == "delete_selected_schedules":
            schedule_ids = request.POST.getlist("schedule_ids")
            if not schedule_ids:
                messages.warning(request, "No schedules selected for deletion.")
                return redirect("dashboard")
            try:
                deleted_count, _ = Schedule.objects.filter(id__in=schedule_ids).delete()
                messages.success(request, f"{deleted_count} schedule(s) deleted successfully.")
            except Exception as e:
                messages.error(request, f"Error deleting schedules: {str(e)}")
            return redirect("dashboard")
        
        # --- Fallback for unknown form_type ---
        else:
            messages.warning(request, "Unknown action attempted.")
            return redirect("dashboard")

    # --- GET Request: Prepare data for dashboard display ---
    reservation_count = Reservation.objects.count()
    user_count = UserModel.objects.count()
    barber_count = Barber.objects.filter(status=Barber.BarberStatus.AVAILABLE).count()
    service_count = Service.objects.count()
    
    barbers_list = Barber.objects.all().prefetch_related('services')
    services_list = Service.objects.all()
    users_list = UserModel.objects.all() # Consider if all users are needed or just customers
    reservations_list = Reservation.objects.select_related('barber', 'reserved_by').prefetch_related('services').order_by('-start_datetime')
    schedules_list = Schedule.objects.select_related('barber').order_by('start_datetime') # Fetch schedules
    
    context = {
        'reservation_count': reservation_count,
        'user_count': user_count,
        'barber_count': barber_count,
        'service_count': service_count,
        'barbers': barbers_list,
        'services': services_list, 
        'users': users_list,
        'reservations': list(reservations_list), # Convert queryset to list if needed for template iteration or JS
        'schedules': schedules_list, # Add schedules to context
    }
    
    return render(request, "receptionist/dashboard.html", context)


# --- API Endpoints ---
@csrf_exempt 
@group_required('Receptionist')
def get_barber(request, barber_id):
    try:
        barber = Barber.objects.prefetch_related('services').get(id=barber_id)
        offered_service_ids = [service.id for service in barber.services.all()]
        profile_picture_url = barber.profile_picture.url if barber.profile_picture else ''
        return JsonResponse({'status': 'success', 'barber': {'id': barber.id, 'first_name': barber.first_name, 'last_name': barber.last_name, 'phone_number': barber.phone_number, 'status': barber.status, 'services': offered_service_ids, 'profile_picture': profile_picture_url }})
    except Barber.DoesNotExist: return JsonResponse({'status': 'error', 'message': 'Barber not found'}, status=404)
    except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
@group_required('Receptionist')
def get_service(request, service_id):
    try:
        service = Service.objects.get(id=service_id)
        return JsonResponse({'status': 'success', 'service': {'id': service.id, 'service_name': service.service_name, 'price': service.price, 'estimated_time': service.estimated_time, 'category': service.category}})
    except Service.DoesNotExist: return JsonResponse({'status': 'error', 'message': 'Service not found'}, status=404)
    except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
@group_required('Receptionist')
def get_reservation(request, reservation_id):
    try:
        reservation = Reservation.objects.select_related('barber', 'reserved_by').prefetch_related('services').get(id=reservation_id)
        start_datetime_formatted = ''
        if reservation.start_datetime:
            start_datetime_formatted = timezone.localtime(reservation.start_datetime).strftime('%Y-%m-%dT%H:%M')

        return JsonResponse({
            'status': 'success',
            'reservation': {
                'id': reservation.id, 'barber_id': reservation.barber.id, 
                'reserved_by_id': reservation.reserved_by.id,
                'reserved_for_first_name': reservation.reserved_for_first_name,
                'reserved_for_last_name': reservation.reserved_for_last_name,
                'reserved_for_email': reservation.reserved_for_email,
                'reserved_for_phone': reservation.reserved_for_phone,
                'is_reserved_for_self': reservation.is_reserved_for_self,
                'start_datetime': start_datetime_formatted,
                'services': [{'id': s.id, 'name': s.service_name} for s in reservation.services.all()],
                'status': reservation.status
            }
        })
    except Reservation.DoesNotExist: return JsonResponse({'status': 'error', 'message': 'Reservation not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# The standalone schedules_view is no longer needed as its logic is merged into receptionist view.
# The standalone update_reservation view is also removed as its logic is handled by form_type='edit_reservation'.
@group_required("Receptionist")
def update_reservation(request, reservation_id):
    try:
        # Get the reservation
        reservation = Reservation.objects.get(id=reservation_id)

        if request.method == "POST":
            # Update reservation fields
            if "barber_id" in request.POST:
                reservation.barber_id = request.POST["barber_id"]

            if "reserved_by_id" in request.POST:
                reservation.reserved_by_id = request.POST["reserved_by_id"]

            if "reserved_for_first_name" in request.POST:
                reservation.reserved_for_first_name = request.POST[
                    "reserved_for_first_name"
                ]

            if "reserved_for_last_name" in request.POST:
                reservation.reserved_for_last_name = request.POST[
                    "reserved_for_last_name"
                ]

            if "reserved_for_email" in request.POST:
                reservation.reserved_for_email = request.POST["reserved_for_email"]

            if "reserved_for_phone" in request.POST:
                reservation.reserved_for_phone = request.POST["reserved_for_phone"]

            reservation.is_reserved_for_self = "is_reserved_for_self" in request.POST

            if "date" in request.POST and "time" in request.POST:
                from datetime import datetime

                start_datetime = datetime.strptime(
                    f"{request.POST['date']} {request.POST['time']}", "%Y-%m-%d %H:%M"
                )
                reservation.start_datetime = start_datetime

            if "status" in request.POST:
                reservation.status = request.POST["status"]

            # Save the reservation
            reservation.save()

            # Update services if provided
            if "services" in request.POST:
                services = request.POST.getlist("services")
                if services:
                    reservation.services.clear()
                    for service_id in services:
                        reservation.services.add(service_id)

            # Calculate end time based on services duration
            total_duration = sum(
                service.duration for service in reservation.services.all()
            )
            from datetime import timedelta

            reservation.end_datetime = reservation.start_datetime + timedelta(
                minutes=total_duration
            )
            reservation.save()

            # Add success message
            messages.success(request, "Reservation updated successfully")

            # Redirect back to the dashboard
            from django.shortcuts import redirect

            return redirect("dashboard")

        # If it's not a POST request, redirect to dashboard
        return redirect("dashboard")
    except Reservation.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Reservation not found"}, status=404
        )
    except Exception as e:
        import traceback

        print(traceback.format_exc())
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
