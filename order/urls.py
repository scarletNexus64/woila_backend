"""
URLs pour le module de commande VTC
"""
from django.urls import path
from . import views

app_name = 'order'

urlpatterns = [
    # ============= DRIVER ENDPOINTS =============
    
    # Status management
    path('driver/status/', views.get_driver_status, name='get_driver_status'),
    path('driver/status/toggle/', views.toggle_driver_status, name='toggle_driver_status'),
    path('driver/status/online/', views.set_driver_online, name='set_driver_online'),
    path('driver/status/offline/', views.set_driver_offline, name='set_driver_offline'),
    
    # Location & tracking
    path('driver/location/update/', views.update_driver_location, name='update_driver_location'),
    
    # Order management
    path('driver/order/<uuid:order_id>/accept/', views.accept_order, name='accept_order'),
    path('driver/order/<uuid:order_id>/reject/', views.reject_order, name='reject_order'),
    path('driver/order/<uuid:order_id>/arrived/', views.driver_arrived, name='driver_arrived'),
    path('driver/order/<uuid:order_id>/start/', views.start_trip, name='start_trip'),
    path('driver/order/<uuid:order_id>/complete/', views.complete_trip, name='complete_trip'),
    
    # Driver history & current
    path('driver/order/current/', views.get_driver_current_order, name='driver_current_order'),
    path('driver/order/history/', views.get_driver_order_history, name='driver_order_history'),
    
    # ============= CUSTOMER ENDPOINTS =============
    
    # Search & estimate
    path('customer/search-drivers/', views.search_drivers, name='search_drivers'),
    path('customer/estimate-price/', views.estimate_price, name='estimate_price'),
    
    # Order management
    path('customer/order/create/', views.create_order, name='create_order'),
    path('customer/order/<uuid:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('customer/order/<uuid:order_id>/track/', views.track_order, name='track_order'),
    path('customer/order/<uuid:order_id>/rate/', views.rate_order, name='rate_order'),
    
    # Customer history
    path('customer/order/history/', views.get_customer_order_history, name='customer_order_history'),
    
    # ============= PAYMENT ENDPOINTS =============
    
    # Process payment
    path('order/<uuid:order_id>/payment/', views.process_payment, name='process_payment'),
    
    # ============= COMMON ENDPOINTS =============
    
    # Payment methods & vehicle types
    path('payment-methods/', views.get_payment_methods, name='payment_methods'),
    path('vehicle-types/available/', views.get_available_vehicle_types, name='available_vehicle_types'),
    
    # Order details (accessible by both driver and customer)
    path('order/<uuid:order_id>/', views.get_order_details, name='order_details'),
]
