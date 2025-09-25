# EXISTING ENDPOINTS - DO NOT MODIFY URLs - Already integrated in production
# Authentication URLs for the Woila VTC platform

from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    # EXISTING ENDPOINT: POST /api/auth/login/ - DO NOT MODIFY
    path('login/', views.LoginView.as_view(), name='login'),
    
    # EXISTING ENDPOINT: POST /api/auth/logout/ - DO NOT MODIFY
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # EXISTING ENDPOINT: POST /api/auth/register/driver/ - DO NOT MODIFY
    path('register/driver/', views.RegisterDriverView.as_view(), name='register-driver'),
    
    # EXISTING ENDPOINT: POST /api/auth/register/customer/ - DO NOT MODIFY
    path('register/customer/', views.RegisterCustomerView.as_view(), name='register-customer'),
    
    # EXISTING ENDPOINT: POST /api/auth/token/verify/ - DO NOT MODIFY
    path('token/verify/', views.TokenVerifyView.as_view(), name='token-verify'),
    
    # EXISTING ENDPOINT: POST /api/auth/token/refresh/ - DO NOT MODIFY
    path('token/refresh/', views.TokenRefreshView.as_view(), name='token-refresh'),
    
    # EXISTING ENDPOINT: POST /api/auth/forgot-password/ - DO NOT MODIFY
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    
    # EXISTING ENDPOINT: POST /api/auth/generate-otp/ - DO NOT MODIFY
    path('generate-otp/', views.GenerateOTPView.as_view(), name='generate-otp'),
    
    # EXISTING ENDPOINT: POST /api/auth/verify-otp/ - DO NOT MODIFY
    path('verify-otp/', views.VerifyOTPView.as_view(), name='verify-otp'),
]