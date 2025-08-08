from django.urls import path
from . import views

app_name = 'order'

urlpatterns = [
    # Driver status management
    path('driver/status/', views.get_driver_status, name='get_driver_status'),
    path('driver/status/toggle/', views.toggle_driver_status, name='toggle_driver_status'),
    path('driver/status/online/', views.set_driver_online, name='set_driver_online'),
    path('driver/status/offline/', views.set_driver_offline, name='set_driver_offline'),
]