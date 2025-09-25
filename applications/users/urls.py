# EXISTING ENDPOINTS - DO NOT MODIFY URLs - Already integrated in production
# User profile management URLs for the Woila VTC platform

from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # EXISTING ENDPOINT: GET /api/auth/me/ - DO NOT MODIFY
    path('me/', views.MeProfileView.as_view(), name='me-profile'),
    
    # EXISTING ENDPOINT: GET /api/profiles/driver/{driver_id}/ - DO NOT MODIFY  
    path('driver/<int:driver_id>/', views.DriverProfileView.as_view(), name='driver-profile'),
    
    # EXISTING ENDPOINT: GET /api/profiles/customer/{customer_id}/ - DO NOT MODIFY
    path('customer/<int:customer_id>/', views.CustomerProfileView.as_view(), name='customer-profile'),
    
    # EXISTING ENDPOINT: GET /api/profiles/drivers/ - DO NOT MODIFY
    path('drivers/', views.AllDriversView.as_view(), name='all-drivers'),
    
    # EXISTING ENDPOINT: GET /api/profiles/customers/ - DO NOT MODIFY
    path('customers/', views.AllCustomersView.as_view(), name='all-customers'),
]