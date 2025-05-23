from django.shortcuts import render
from core.decorators import group_required

# Create your views here.

@group_required('Receptionist')
def receptionist(request):
    return render(request, "receptionist/index.html")


