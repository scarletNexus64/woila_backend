from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LoginView,
    RegisterDriverView,
    RegisterCustomerView, 
    LogoutView,
    TokenVerifyView,
    TokenRefreshView,
    DocumentImportView,
    DocumentListView,
    VehicleCreateView,
    VehicleListView,
    VehicleDetailView,
    VehiclesByDriverView,
    DriverProfileView,
    CustomerProfileView,
    AllDriversView,
    AllCustomersView
)
from .viewsets.referral import ReferralViewSet

# Router pour les ViewSets
router = DefaultRouter()
router.register(r'referral', ReferralViewSet, basename='referral')

urlpatterns = [
    # Router endpoints (ViewSets)
    path('', include(router.urls)),
    
    # Authentication endpoints
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    
    # Registration endpoints
    path('auth/register/driver/', RegisterDriverView.as_view(), name='register-driver'),
    path('auth/register/customer/', RegisterCustomerView.as_view(), name='register-customer'),
    
    # Token management endpoints
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token-verify'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # Document management endpoints
    path('documents/import/', DocumentImportView.as_view(), name='document-import'),
    path('documents/list/', DocumentListView.as_view(), name='document-list'),
    
    # Vehicle management endpoints
    path('vehicles/', VehicleListView.as_view(), name='vehicle-list'),
    path('vehicles/create/', VehicleCreateView.as_view(), name='vehicle-create'),
    path('vehicles/<int:vehicle_id>/', VehicleDetailView.as_view(), name='vehicle-detail'),
    path('vehicles/driver/<int:driver_id>/', VehiclesByDriverView.as_view(), name='vehicles-by-driver'),
    
    # Profile management endpoints
    path('profiles/driver/<int:driver_id>/', DriverProfileView.as_view(), name='driver-profile'),
    path('profiles/customer/<int:customer_id>/', CustomerProfileView.as_view(), name='customer-profile'),
    path('profiles/drivers/', AllDriversView.as_view(), name='all-drivers'),
    path('profiles/customers/', AllCustomersView.as_view(), name='all-customers'),
]