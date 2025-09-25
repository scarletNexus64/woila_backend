# NEW ORGANIZED URL STRUCTURE - Future replacement for urls.py
# This file shows the new organized URL structure with proper app separation
# EXISTING ENDPOINTS are preserved with comments indicating they should not be modified

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API Documentation - EXISTING ENDPOINTS
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # NEW ORGANIZED STRUCTURE - Proper Django app organization
    # All existing endpoints are preserved with same URLs
    
    # Authentication endpoints - EXISTING URLs preserved
    path('api/auth/', include('authentication.urls')),
    
    # User profile endpoints - EXISTING URLs preserved  
    path('api/profiles/', include('users.urls')),
    path('api/auth/', include('users.urls')),  # For /api/auth/me/
    
    # Vehicle endpoints - EXISTING URLs preserved
    path('api/vehicles/', include('vehicles.urls')),
    
    # Notification & FCM endpoints - EXISTING URLs preserved
    path('api/notifications/', include('notifications.urls')),
    path('api/fcm/', include('notifications.urls')),  # FCM URLs are under notifications app
    
    # Wallet endpoints - EXISTING URLs preserved
    path('api/wallet/', include('wallet.urls')),
    
    # Order/Rides endpoints - EXISTING URLs preserved (keeping original order app)
    path('api/', include('order.urls')),
    
    # Legacy API endpoints (to be gradually deprecated)
    # These maintain backward compatibility
    path('api/', include('api.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)