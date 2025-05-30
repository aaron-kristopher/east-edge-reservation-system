from django.shortcuts import render
from django.http import JsonResponse
from core.decorators import group_required
from barbers.models import Barber, Service
from reservations.models import Reservation
from customers.models import UserModel
from django.db.models import Count
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

# Create your views here.

@group_required('Receptionist')
def receptionist(request):
    # Get counts for dashboard
    reservation_count = Reservation.objects.count()  # Count all reservations
    user_count = UserModel.objects.count()
    barber_count = Barber.objects.filter(status='A').count()  # Only count available barbers
    service_count = Service.objects.count()
    
    # Get all barbers for the barbers section
    barbers = Barber.objects.all().prefetch_related('services')
    
    # Get all services for the services section
    services = Service.objects.all()
    
    # Get all users for the reservation form
    users = UserModel.objects.all()
    
    # Get all reservations for the reservations section
    reservations = Reservation.objects.all().select_related('barber', 'reserved_by').prefetch_related('services')
    
    # Handle form submission for editing reservations
    if request.method == 'POST' and 'form_type' in request.POST:
        form_type = request.POST['form_type']
        
        # Handle editing a reservation
        if form_type == 'edit_reservation':
            reservation_id = request.POST.get('reservation_id')
            try:
                reservation = Reservation.objects.get(id=reservation_id)
                
                # Update reservation fields
                barber_id = request.POST.get('barber_id')
                if barber_id:
                    reservation.barber_id = barber_id
                    
                reserved_by_id = request.POST.get('reserved_by_id')
                if reserved_by_id:
                    reservation.reserved_by_id = reserved_by_id
                    
                reservation.reserved_for_first_name = request.POST.get('reserved_for_first_name', '')
                reservation.reserved_for_last_name = request.POST.get('reserved_for_last_name', '')
                reservation.reserved_for_email = request.POST.get('reserved_for_email', '')
                reservation.reserved_for_phone = request.POST.get('reserved_for_phone', '')
                reservation.is_reserved_for_self = 'is_reserved_for_self' in request.POST
                
                # Update date and time
                date_str = request.POST.get('date')
                time_str = request.POST.get('time')
                if date_str and time_str:
                    from datetime import datetime
                    start_datetime = datetime.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M')
                    reservation.start_datetime = start_datetime
                
                # Update status
                status = request.POST.get('status')
                if status:
                    reservation.status = status
                
                # Save the reservation
                reservation.save()
                
                # Update services
                service_ids = request.POST.getlist('services')
                if service_ids:
                    reservation.services.clear()
                    for service_id in service_ids:
                        reservation.services.add(service_id)
                
                # Add success message
                from django.contrib import messages
                messages.success(request, 'Reservation updated successfully')
                
            except Reservation.DoesNotExist:
                from django.contrib import messages
                messages.error(request, 'Reservation not found')
            except Exception as e:
                from django.contrib import messages
                messages.error(request, f'Error updating reservation: {str(e)}')
        
        # Handle adding a new service
        elif form_type == 'add_service':
            try:
                # Create a new service
                service = Service()
                service.service_name = request.POST.get('service_name', '')
                service.price = float(request.POST.get('price', 0))
                service.estimated_time = int(request.POST.get('estimated_time', 0))
                service.category = request.POST.get('category', 'H')
                
                # Save the service
                service.save()
                
                # Add success message
                from django.contrib import messages
                messages.success(request, 'Service added successfully')
                
            except Exception as e:
                from django.contrib import messages
                messages.error(request, f'Error adding service: {str(e)}')
        
        # Handle editing a service
        elif form_type == 'edit_service':
            service_id = request.POST.get('service_id')
            try:
                service = Service.objects.get(id=service_id)
                
                # Update service fields
                service.service_name = request.POST.get('service_name', '')
                service.price = float(request.POST.get('price', 0))
                service.estimated_time = int(request.POST.get('estimated_time', 0))
                service.category = request.POST.get('category', 'H')
                
                # Save the service
                service.save()
                
                # Add success message
                from django.contrib import messages
                messages.success(request, 'Service updated successfully')
                
            except Service.DoesNotExist:
                from django.contrib import messages
                messages.error(request, 'Service not found')
            except Exception as e:
                from django.contrib import messages
                messages.error(request, f'Error updating service: {str(e)}')
        
        # Handle deleting a single service
        elif form_type == 'delete_service':
            service_id = request.POST.get('service_id')
            try:
                service = Service.objects.get(id=service_id)
                service.delete()
                
                # Add success message
                from django.contrib import messages
                messages.success(request, 'Service deleted successfully')
            except Service.DoesNotExist:
                from django.contrib import messages
                messages.error(request, 'Service not found')
            except Exception as e:
                from django.contrib import messages
                messages.error(request, f'Error deleting service: {str(e)}')
        
        # Handle deleting multiple services
        elif form_type == 'delete_services':
            service_ids = request.POST.getlist('selected_services')
            if service_ids:
                try:
                    # Delete all selected services
                    deleted_count = 0
                    for service_id in service_ids:
                        try:
                            service = Service.objects.get(id=service_id)
                            service.delete()
                            deleted_count += 1
                        except Service.DoesNotExist:
                            pass
                    
                    # Add success message
                    from django.contrib import messages
                    messages.success(request, f'{deleted_count} service(s) deleted successfully')
                except Exception as e:
                    from django.contrib import messages
                    messages.error(request, f'Error deleting services: {str(e)}')
        
        # Handle deleting multiple reservations
        elif form_type == 'delete_reservations':
            reservation_ids = request.POST.getlist('reservation_ids')
            if reservation_ids:
                try:
                    # Delete all selected reservations
                    deleted_count = 0
                    for reservation_id in reservation_ids:
                        try:
                            reservation = Reservation.objects.get(id=reservation_id)
                            reservation.delete()
                            deleted_count += 1
                        except Reservation.DoesNotExist:
                            pass
                    
                    # Add success message
                    from django.contrib import messages
                    messages.success(request, f'{deleted_count} reservation(s) deleted successfully')
                except Exception as e:
                    from django.contrib import messages
                    messages.error(request, f'Error deleting reservations: {str(e)}')
        
        # Handle editing a barber
        elif form_type == 'edit_barber':
            barber_id = request.POST.get('barber_id')
            try:
                barber = Barber.objects.get(id=barber_id)
                
                # Update barber fields
                barber.first_name = request.POST.get('first_name', '')
                barber.last_name = request.POST.get('last_name', '')
                barber.phone_number = request.POST.get('phone_number', '')
                barber.status = request.POST.get('status', 'A')
                
                # Handle profile picture
                if 'remove_profile_picture' in request.POST:
                    # Remove the current profile picture
                    barber.profile_picture = None
                elif 'profile_picture' in request.FILES:
                    # With ImageField, we can directly assign the file
                    barber.profile_picture = request.FILES['profile_picture']
                
                # Save the barber
                barber.save()
                
                # Update services
                service_ids = request.POST.getlist('services')
                if service_ids:
                    barber.services.clear()
                    for service_id in service_ids:
                        barber.services.add(service_id)
                
                # Add success message
                from django.contrib import messages
                messages.success(request, 'Barber updated successfully')
                
            except Barber.DoesNotExist:
                from django.contrib import messages
                messages.error(request, 'Barber not found')
            except Exception as e:
                from django.contrib import messages
                messages.error(request, f'Error updating barber: {str(e)}')
        
        # Handle deleting a single barber
        elif form_type == 'delete_barber':
            barber_id = request.POST.get('barber_id')
            try:
                barber = Barber.objects.get(id=barber_id)
                barber.delete()
                
                # Add success message
                from django.contrib import messages
                messages.success(request, 'Barber deleted successfully')
            except Barber.DoesNotExist:
                from django.contrib import messages
                messages.error(request, 'Barber not found')
            except Exception as e:
                from django.contrib import messages
                messages.error(request, f'Error deleting barber: {str(e)}')
        
        # Handle deleting multiple barbers
        elif form_type == 'delete_barbers':
            barber_ids = request.POST.getlist('selected_barbers')
            if barber_ids:
                try:
                    # Delete all selected barbers
                    deleted_count = 0
                    for barber_id in barber_ids:
                        try:
                            barber = Barber.objects.get(id=barber_id)
                            barber.delete()
                            deleted_count += 1
                        except Barber.DoesNotExist:
                            pass
                    
                    # Add success message
                    from django.contrib import messages
                    messages.success(request, f'{deleted_count} barber(s) deleted successfully')
                except Exception as e:
                    from django.contrib import messages
                    messages.error(request, f'Error deleting barbers: {str(e)}')
        
        # Handle adding a new barber
        elif form_type == 'add_barber':
            try:
                # Create a new barber
                barber = Barber()
                barber.first_name = request.POST.get('first_name', '')
                barber.last_name = request.POST.get('last_name', '')
                barber.phone_number = request.POST.get('phone_number', '')
                barber.status = request.POST.get('status', 'A')
                
                # Handle profile picture if provided
                if 'profile_picture' in request.FILES:
                    barber.profile_picture = request.FILES['profile_picture']
                
                # Save the barber
                barber.save()
                
                # Add services
                service_ids = request.POST.getlist('services')
                if service_ids:
                    for service_id in service_ids:
                        barber.services.add(service_id)
                
                # Add success message
                from django.contrib import messages
                messages.success(request, 'Barber added successfully')
                
            except Exception as e:
                from django.contrib import messages
                messages.error(request, f'Error adding barber: {str(e)}')
        
        # Handle adding a new service
        elif form_type == 'add_service':
            try:
                # Create a new service
                service = Service()
                service.service_name = request.POST.get('service_name', '')
                service.price = float(request.POST.get('price', 0))
                service.estimated_time = int(request.POST.get('estimated_time', 0))
                service.category = request.POST.get('category', 'H')
                
                # Save the service
                service.save()
                
                # Add success message
                from django.contrib import messages
                messages.success(request, 'Service added successfully')
                
            except Exception as e:
                from django.contrib import messages
                messages.error(request, f'Error adding service: {str(e)}')
        
        # Handle editing a service
        elif form_type == 'edit_service':
            service_id = request.POST.get('service_id')
            try:
                service = Service.objects.get(id=service_id)
                
                # Update service fields
                service.service_name = request.POST.get('service_name', '')
                service.price = float(request.POST.get('price', 0))
                service.estimated_time = int(request.POST.get('estimated_time', 0))
                service.category = request.POST.get('category', 'H')
                
                # Save the service
                service.save()
                
                # Add success message
                from django.contrib import messages
                messages.success(request, 'Service updated successfully')
                
            except Service.DoesNotExist:
                from django.contrib import messages
                messages.error(request, 'Service not found')
            except Exception as e:
                from django.contrib import messages
                messages.error(request, f'Error updating service: {str(e)}')
        
        # Handle deleting a single service
        elif form_type == 'delete_service':
            service_id = request.POST.get('service_id')
            try:
                service = Service.objects.get(id=service_id)
                service.delete()
                
                # Add success message
                from django.contrib import messages
                messages.success(request, 'Service deleted successfully')
            except Service.DoesNotExist:
                from django.contrib import messages
                messages.error(request, 'Service not found')
            except Exception as e:
                from django.contrib import messages
                messages.error(request, f'Error deleting service: {str(e)}')
        
        # Handle deleting multiple services
        elif form_type == 'delete_services':
            service_ids = request.POST.getlist('selected_services')
            if service_ids:
                try:
                    # Delete all selected services
                    deleted_count = 0
                    for service_id in service_ids:
                        try:
                            service = Service.objects.get(id=service_id)
                            service.delete()
                            deleted_count += 1
                        except Service.DoesNotExist:
                            pass
                    
                    # Add success message
                    from django.contrib import messages
                    messages.success(request, f'{deleted_count} service(s) deleted successfully')
                except Exception as e:
                    from django.contrib import messages
                    messages.error(request, f'Error deleting services: {str(e)}')
    
    context = {
        'reservation_count': reservation_count,
        'user_count': user_count,
        'barber_count': barber_count,
        'service_count': service_count,
        'barbers': barbers,
        'services': services,
        'users': users,
        'reservations': reservations,
    }
    
    return render(request, "receptionist/dashboard.html", context)

@group_required('Receptionist')
def schedule(request):
    return render(request, "receptionist/reservations.html")

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@group_required('Receptionist')
def get_barber(request, barber_id):
    try:
        # Get the barber
        barber = Barber.objects.get(id=barber_id)
        
        # Get the barber's services
        services = [service.id for service in barber.services.all()]
        
        # Get profile picture URL if available
        profile_picture_url = ''
        if barber.profile_picture:
            profile_picture_url = barber.profile_picture.url
        
        # Create a response with the barber data
        return JsonResponse({
            'status': 'success',
            'barber': {
                'id': barber.id,
                'first_name': barber.first_name,
                'last_name': barber.last_name,
                'phone_number': barber.phone_number,
                'status': barber.status,
                'services': services,
                'profile_picture': profile_picture_url
            }
        })
    except Barber.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Barber not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@group_required('Receptionist')
def get_service(request, service_id):
    try:
        # Get the service
        service = Service.objects.get(id=service_id)
        
        # Create a response with the service data
        return JsonResponse({
            'status': 'success',
            'service': {
                'id': service.id,
                'service_name': service.service_name,
                'price': service.price,
                'estimated_time': service.estimated_time,
                'category': service.category
            }
        })
    except Service.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Service not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@group_required('Receptionist')
def get_reservation(request, reservation_id):
    try:
        # Get the reservation
        reservation = Reservation.objects.get(id=reservation_id)
        
        # Create a response with the reservation data
        return JsonResponse({
            'status': 'success',
            'reservation': {
                'id': reservation.id,
                'barber_id': reservation.barber.id,
                'reserved_by_id': reservation.reserved_by.id,
                'reserved_for_first_name': reservation.reserved_for_first_name,
                'reserved_for_last_name': reservation.reserved_for_last_name,
                'reserved_for_email': reservation.reserved_for_email,
                'reserved_for_phone': reservation.reserved_for_phone,
                'is_reserved_for_self': reservation.is_reserved_for_self,
                'start_datetime': reservation.start_datetime.strftime('%Y-%m-%dT%H:%M:%S'),
                'services': [{'id': service.id, 'name': service.service_name} for service in reservation.services.all()],
                'status': reservation.status
            }
        })
    except Reservation.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Reservation not found'}, status=404)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@group_required('Receptionist')
def update_reservation(request, reservation_id):
    try:
        # Get the reservation
        reservation = Reservation.objects.get(id=reservation_id)
        
        if request.method == 'POST':
            # Update reservation fields
            if 'barber_id' in request.POST:
                reservation.barber_id = request.POST['barber_id']
                
            if 'reserved_by_id' in request.POST:
                reservation.reserved_by_id = request.POST['reserved_by_id']
                
            if 'reserved_for_first_name' in request.POST:
                reservation.reserved_for_first_name = request.POST['reserved_for_first_name']
                
            if 'reserved_for_last_name' in request.POST:
                reservation.reserved_for_last_name = request.POST['reserved_for_last_name']
                
            if 'reserved_for_email' in request.POST:
                reservation.reserved_for_email = request.POST['reserved_for_email']
                
            if 'reserved_for_phone' in request.POST:
                reservation.reserved_for_phone = request.POST['reserved_for_phone']
                
            reservation.is_reserved_for_self = 'is_reserved_for_self' in request.POST
                
            if 'date' in request.POST and 'time' in request.POST:
                from datetime import datetime
                start_datetime = datetime.strptime(f"{request.POST['date']} {request.POST['time']}", "%Y-%m-%d %H:%M")
                reservation.start_datetime = start_datetime
                
            if 'status' in request.POST:
                reservation.status = request.POST['status']
                
            # Save the reservation
            reservation.save()
            
            # Update services if provided
            if 'services' in request.POST:
                services = request.POST.getlist('services')
                if services:
                    reservation.services.clear()
                    for service_id in services:
                        reservation.services.add(service_id)
        
            # Calculate end time based on services duration
            total_duration = sum(service.duration for service in reservation.services.all())
            from datetime import timedelta
            reservation.end_datetime = reservation.start_datetime + timedelta(minutes=total_duration)
            reservation.save()
            
            # Add success message
            from django.contrib import messages
            messages.success(request, 'Reservation updated successfully')
            
            # Redirect back to the dashboard
            from django.shortcuts import redirect
            return redirect('dashboard')
        
        # If it's not a POST request, redirect to dashboard
        return redirect('dashboard')
    except Reservation.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Reservation not found'}, status=404)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)