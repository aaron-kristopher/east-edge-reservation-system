"""
URL configuration for east_edge_reservation project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from customers import views
from receptionist import views as receptionist_views

urlpatterns = [
    path("", include("customers.urls")),
    path("barbers/", include("barbers.urls")),
    # path("reservations/", include("reservations.urls")),
    path("admin/", admin.site.urls),
    #logging in 
    path('accounts/login/', views.customer_login, name="login"),
    path('accounts/logout/', views.customer_logout, name="logout"),
    # API endpoints
    path('api/barber/<int:barber_id>/', receptionist_views.get_barber, name='get_barber'),
    path('api/service/<int:service_id>/', receptionist_views.get_service, name='get_service'),
    path('api/reservation/<int:reservation_id>/', receptionist_views.get_reservation, name='get_reservation'),
    path('accounts/signup/', views.customer_signup, name="signup"),
    path('', include('reservations.urls')),
    path('', include("receptionist.urls"))
] 

# Add media serving in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
