from django.shortcuts import render

# Import all viewsets
from .viewsets.login import LoginView
from .viewsets.register import RegisterDriverView, RegisterCustomerView
from .viewsets.logout import LogoutView
from .viewsets.token import TokenVerifyView, TokenRefreshView
from .viewsets.documents import DocumentImportView, DocumentListView
from .viewsets.vehicles import VehicleCreateView, VehicleListView, VehicleDetailView, VehiclesByDriverView

# Export views for URL configuration
__all__ = [
    'LoginView',
    'RegisterDriverView', 
    'RegisterCustomerView',
    'LogoutView',
    'TokenVerifyView',
    'TokenRefreshView',
    'DocumentImportView',
    'DocumentListView',
    'VehicleCreateView',
    'VehicleListView',
    'VehicleDetailView',
    'VehiclesByDriverView'
]
