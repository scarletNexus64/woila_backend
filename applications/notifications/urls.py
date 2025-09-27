# EXISTING ENDPOINTS - DO NOT MODIFY URLs - Already integrated in production
# Notification management URLs for the Woila VTC platform

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Notification endpoints
    # EXISTING ENDPOINT: GET /api/notifications/ - DO NOT MODIFY
    path('', views.NotificationListView.as_view(), name='notification-list'),
    
    # EXISTING ENDPOINT: GET /api/notifications/unread/ - DO NOT MODIFY
    path('unread/', views.NotificationUnreadView.as_view(), name='notification-unread'),
    
    # EXISTING ENDPOINT: GET /api/notifications/stats/ - DO NOT MODIFY
    path('stats/', views.NotificationStatsView.as_view(), name='notification-stats'),
    
    # EXISTING ENDPOINT: POST /api/notifications/mark-all-read/ - DO NOT MODIFY
    path('mark-all-read/', views.NotificationMarkAllReadView.as_view(), name='notification-mark-all-read'),
    
    # EXISTING ENDPOINT: GET /api/notifications/{notification_id}/ - DO NOT MODIFY
    path('<int:notification_id>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    
    # FCM Token endpoints  
    # EXISTING ENDPOINT: POST /api/fcm/register/ - DO NOT MODIFY
    path('fcm/register/', views.FCMTokenRegisterView.as_view(), name='fcm-register'),
    
    # EXISTING ENDPOINT: POST /api/fcm/unregister/ - DO NOT MODIFY
    path('fcm/unregister/', views.FCMTokenUnregisterView.as_view(), name='fcm-unregister'),
    
    # EXISTING ENDPOINT: GET /api/fcm/tokens/ - DO NOT MODIFY
    path('fcm/tokens/', views.FCMTokenListView.as_view(), name='fcm-tokens'),
    
    # EXISTING ENDPOINT: GET /api/fcm/tokens/{token_id}/ - DO NOT MODIFY
    path('fcm/tokens/<int:token_id>/', views.FCMTokenDetailView.as_view(), name='fcm-token-detail'),
    
    # EXISTING ENDPOINT: POST /api/fcm/test-notification/ - DO NOT MODIFY
    path('fcm/test-notification/', views.FCMTestNotificationView.as_view(), name='fcm-test'),
]