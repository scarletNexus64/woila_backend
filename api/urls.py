from django.urls import path
from .views import (
    LoginView,
    RegisterDriverView,
    RegisterCustomerView, 
    LogoutView,
    TokenVerifyView,
    TokenRefreshView,
    DocumentImportView,
    DocumentListView
)

urlpatterns = [
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
]