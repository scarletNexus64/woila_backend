from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/driver/(?P<driver_id>\w+)/$', consumers.DriverConsumer.as_asgi()),
    re_path(r'ws/customer/(?P<customer_id>\w+)/$', consumers.CustomerConsumer.as_asgi()),
]