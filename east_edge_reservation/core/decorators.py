from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from functools import wraps

def group_required(group_names):
    """
    Decorator to check if a user belongs to required groups
    Usage: @group_required(['Customer']) or @group_required(['Receptionist', 'Barber'])
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')  # Replace 'login' with your login URL name
            
            # Check if the user belongs to any of the required groups
            if isinstance(group_names, str):
                groups = [group_names]
            else:
                groups = group_names

            if request.user.groups.filter(name__in=groups).exists() or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return _wrapped_view
    return decorator
