from django.contrib import admin
from .models import Order, DriverStatus, OrderTracking


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'customer', 'driver', 'status', 'total_price', 
        'estimated_distance_km', 'created_at'
    ]
    list_filter = [
        'status', 'is_night_fare', 'vehicle_type', 'city', 
        'vip_zone', 'created_at'
    ]
    search_fields = [
        'customer__name', 'customer__surname', 'customer__phone_number',
        'driver__name', 'driver__surname', 'driver__phone_number',
        'pickup_address', 'destination_address'
    ]
    readonly_fields = [
        'id', 'created_at', 'accepted_at', 'started_at', 
        'completed_at', 'cancelled_at'
    ]
    
    fieldsets = (
        ('📋 Informations générales', {
            'fields': ('id', 'customer', 'driver', 'status')
        }),
        ('📍 Localisation', {
            'fields': (
                ('pickup_address', 'pickup_latitude', 'pickup_longitude'),
                ('destination_address', 'destination_latitude', 'destination_longitude')
            )
        }),
        ('🚗 Configuration', {
            'fields': ('vehicle_type', 'city', 'vip_zone')
        }),
        ('💰 Tarification', {
            'fields': (
                ('estimated_distance_km', 'actual_distance_km'),
                ('base_price', 'distance_price'),
                ('vehicle_additional_price', 'city_price', 'vip_zone_price'),
                ('total_price', 'is_night_fare')
            )
        }),
        ('⏰ Timestamps', {
            'fields': (
                'created_at', 'accepted_at', 'started_at', 
                'completed_at', 'cancelled_at'
            )
        }),
        ('📝 Notes', {
            'fields': ('customer_notes', 'driver_notes', 'cancellation_reason'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'customer', 'driver', 'vehicle_type', 'city', 'vip_zone'
        )


@admin.register(DriverStatus)
class DriverStatusAdmin(admin.ModelAdmin):
    list_display = [
        'driver', 'status', 'current_latitude', 'current_longitude',
        'last_location_update', 'last_online'
    ]
    list_filter = ['status', 'last_online', 'updated_at']
    search_fields = [
        'driver__name', 'driver__surname', 'driver__phone_number'
    ]
    readonly_fields = [
        'websocket_channel', 'last_location_update', 'last_online', 'updated_at'
    ]
    
    fieldsets = (
        ('👤 Chauffeur', {
            'fields': ('driver', 'status')
        }),
        ('📍 Position', {
            'fields': ('current_latitude', 'current_longitude', 'last_location_update')
        }),
        ('🔗 Connexion', {
            'fields': ('websocket_channel', 'last_online', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    list_display = [
        'order', 'event_type', 'latitude', 'longitude', 'created_at'
    ]
    list_filter = ['event_type', 'created_at']
    search_fields = ['order__id', 'notes']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('📋 Événement', {
            'fields': ('order', 'event_type', 'created_at')
        }),
        ('📍 Position', {
            'fields': ('latitude', 'longitude')
        }),
        ('📊 Données', {
            'fields': ('metadata', 'notes'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order')
