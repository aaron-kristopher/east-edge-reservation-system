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
from customers import views

urlpatterns = [
    path("", include("customers.urls")),
    path("barbers/", include("barbers.urls")),
    # path("reservations/", include("reservations.urls")),
    path("admin/", admin.site.urls),
    #logging in 
    path('accounts/login/', views.customer_login, name="login"),
    path('accounts/logout/', views.customer_logout, name="logout"),
    path('accounts/signup/', views.customer_signup, name="signup"),
    
    path('', include('reservations.urls')),

]
