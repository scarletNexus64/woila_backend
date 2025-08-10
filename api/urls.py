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
    AllDriversView,
    AllCustomersView,
    ForgotPasswordView
)
from .viewsets.otp import (
    GenerateOTPView,
    VerifyOTPView
)
from .viewsets.vehicles import (
    VehicleCreateView,
    VehicleListView,
    VehicleDetailView,
    VehiclesByDriverView,
    VehicleUpdateView,
    VehicleDeleteView,
    VehicleDeactivateView,
    VehicleToggleOnlineView,
    VehicleToggleOfflineView,
    VehicleTypeListView,
    VehicleBrandListView,
    VehicleModelListView,
    VehicleColorListView
)
from .viewsets.profiles import (
    DriverProfileView,
    CustomerProfileView
)
from .viewsets.referral import ReferralViewSet
from .viewsets.notifications import (
    NotificationListView,
    NotificationUnreadView,
    NotificationDetailView,
    NotificationMarkAllReadView,
    NotificationStatsView
)
from .viewsets.fcm import (
    FCMTokenRegisterView,
    FCMTokenUnregisterView,
    FCMTokenListView,
    FCMTokenDetailView,
    FCMTestNotificationView
)

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
    path('vehicles/<int:vehicle_id>/update/', VehicleUpdateView.as_view(), name='vehicle-update'),
    path('vehicles/<int:vehicle_id>/delete/', VehicleDeleteView.as_view(), name='vehicle-delete'),
    path('vehicles/<int:vehicle_id>/deactivate/', VehicleDeactivateView.as_view(), name='vehicle-deactivate'),
    path('vehicles/<int:vehicle_id>/toggle-online/', VehicleToggleOnlineView.as_view(), name='vehicle-toggle-online'),
    path('vehicles/<int:vehicle_id>/toggle-offline/', VehicleToggleOfflineView.as_view(), name='vehicle-toggle-offline'),
    path('vehicles/driver/<int:driver_id>/', VehiclesByDriverView.as_view(), name='vehicles-by-driver'),

    # Vehicle Config endpoints
    path('vehicles/configs/types/', VehicleTypeListView.as_view(), name='vehicle-types-list'),
    path('vehicles/configs/brands/', VehicleBrandListView.as_view(), name='vehicle-brands-list'),
    path('vehicles/configs/models/', VehicleModelListView.as_view(), name='vehicle-models-list'),
    path('vehicles/configs/colors/', VehicleColorListView.as_view(), name='vehicle-colors-list'),
    
    # Profile management endpoints
    path('profiles/driver/<int:driver_id>/', DriverProfileView.as_view(), name='driver-profile'),
    path('profiles/customer/<int:customer_id>/', CustomerProfileView.as_view(), name='customer-profile'),
    path('profiles/drivers/', AllDriversView.as_view(), name='all-drivers'),
    path('profiles/customers/', AllCustomersView.as_view(), name='all-customers'),
    
    # OTP endpoints
    path('auth/generate-otp/', GenerateOTPView.as_view(), name='generate-otp'),
    path('auth/verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    
    # Forgot password endpoint
    path('auth/forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    
    # Notification endpoints
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/unread/', NotificationUnreadView.as_view(), name='notification-unread'),
    path('notifications/stats/', NotificationStatsView.as_view(), name='notification-stats'),
    path('notifications/mark-all-read/', NotificationMarkAllReadView.as_view(), name='notification-mark-all-read'),
    path('notifications/<int:notification_id>/', NotificationDetailView.as_view(), name='notification-detail'),
    
    # FCM Token endpoints
    path('fcm/register/', FCMTokenRegisterView.as_view(), name='fcm-register'),
    path('fcm/unregister/', FCMTokenUnregisterView.as_view(), name='fcm-unregister'),
    path('fcm/tokens/', FCMTokenListView.as_view(), name='fcm-tokens'),
    path('fcm/tokens/<int:token_id>/', FCMTokenDetailView.as_view(), name='fcm-token-detail'),
    path('fcm/test-notification/', FCMTestNotificationView.as_view(), name='fcm-test'),
]