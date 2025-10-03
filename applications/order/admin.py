from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    Order, DriverStatus, CustomerStatus, OrderTracking, PaymentMethod, 
    Rating, TripTracking, DriverPool
)


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['type', 'name', 'is_active', 'min_amount', 'max_amount', 'created_at']
    list_filter = ['is_active', 'type', 'created_at']
    search_fields = ['name', 'type']
    list_editable = ['is_active']
    actions = ['delete_all_selected']

    @admin.action(description='🗑️ Supprimer tous les éléments sélectionnés')
    def delete_all_selected(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} méthode(s) de paiement supprimée(s) avec succès.')

    fieldsets = (
        ('📝 Informations générales', {
            'fields': ('type', 'name', 'description', 'icon')
        }),
        ('💰 Limites', {
            'fields': ('min_amount', 'max_amount', 'is_active')
        }),
        ('⏰ Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'customer_link', 'driver_link', 'status_badge', 
        'payment_status_badge', 'total_price', 'final_price',
        'estimated_distance_km', 'created_at'
    ]
    list_filter = [
        'status', 'payment_status', 'is_night_fare', 'vehicle_type', 
        'city', 'vip_zone', 'created_at', 'payment_method'
    ]
    search_fields = [
        'id', 'customer__name', 'customer__surname', 'customer__phone_number',
        'driver__name', 'driver__surname', 'driver__phone_number',
        'pickup_address', 'destination_address'
    ]
    readonly_fields = [
        'id', 'created_at', 'accepted_at', 'driver_arrived_at', 
        'started_at', 'completed_at', 'cancelled_at', 'paid_at'
    ]
    
    fieldsets = (
        ('📋 Informations générales', {
            'fields': ('id', 'customer', 'driver', 'status', 'payment_method', 'payment_status')
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
                ('waiting_time', 'waiting_price'),
                ('total_price', 'final_price'),
                'is_night_fare'
            )
        }),
        ('⭐ Évaluations', {
            'fields': (
                ('driver_rating', 'customer_rating'),
            )
        }),
        ('⏰ Timestamps', {
            'fields': (
                'created_at', 'accepted_at', 'driver_arrived_at',
                'started_at', 'completed_at', 'cancelled_at', 'paid_at'
            )
        }),
        ('📝 Notes', {
            'fields': ('customer_notes', 'driver_notes', 'cancellation_reason'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_completed', 'mark_as_cancelled', 'recalculate_final_price', 'delete_all_selected']

    @admin.action(description='🗑️ Supprimer tous les éléments sélectionnés')
    def delete_all_selected(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} commande(s) supprimée(s) avec succès.')

    def order_number(self, obj):
        return format_html('<strong>#{}</strong>', str(obj.id)[:8])
    order_number.short_description = 'N° Commande'
    
    def customer_link(self, obj):
        if obj.customer:
            url = reverse('admin:users_usercustomer_change', args=[obj.customer.pk])
            return format_html('<a href="{}">{}</a>', url, obj.customer)
        return '-'
    customer_link.short_description = 'Client'
    
    def driver_link(self, obj):
        if obj.driver:
            url = reverse('admin:users_userdriver_change', args=[obj.driver.pk])
            return format_html('<a href="{}">{}</a>', url, obj.driver)
        return '-'
    driver_link.short_description = 'Chauffeur'
    
    def status_badge(self, obj):
        colors = {
            'DRAFT': 'gray',
            'PENDING': 'orange',
            'ACCEPTED': 'blue',
            'DRIVER_ARRIVED': 'purple',
            'IN_PROGRESS': 'cyan',
            'COMPLETED': 'green',
            'CANCELLED': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Statut'
    
    def payment_status_badge(self, obj):
        colors = {
            'PENDING': 'orange',
            'PROCESSING': 'blue',
            'PAID': 'green',
            'FAILED': 'red',
            'REFUNDED': 'purple',
        }
        color = colors.get(obj.payment_status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_payment_status_display()
        )
    payment_status_badge.short_description = 'Paiement'
    
    def mark_as_completed(self, request, queryset):
        queryset.update(status='COMPLETED', completed_at=timezone.now())
        self.message_user(request, f"{queryset.count()} commande(s) marquée(s) comme terminée(s)")
    mark_as_completed.short_description = "Marquer comme terminée"
    
    def mark_as_cancelled(self, request, queryset):
        queryset.update(status='CANCELLED', cancelled_at=timezone.now())
        self.message_user(request, f"{queryset.count()} commande(s) annulée(s)")
    mark_as_cancelled.short_description = "Annuler la commande"
    
    def recalculate_final_price(self, request, queryset):
        for order in queryset:
            order.calculate_final_price()
            order.save()
        self.message_user(request, f"Prix recalculés pour {queryset.count()} commande(s)")
    recalculate_final_price.short_description = "Recalculer le prix final"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'customer', 'driver', 'vehicle_type', 'city', 'vip_zone', 'payment_method'
        )


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = [
        'order_link', 'rating_type', 'score_stars', 'rater_info',
        'rated_info', 'created_at'
    ]
    list_filter = [
        'rating_type', 'score', 'is_anonymous', 'created_at',
        'punctuality', 'driving_quality', 'vehicle_cleanliness', 'communication'
    ]
    search_fields = [
        'order__id', 'comment',
        'rater__name', 'rater__surname',
        'rated_driver__name', 'rated_driver__surname',
        'rated_customer__name', 'rated_customer__surname'
    ]
    readonly_fields = ['created_at', 'updated_at']
    actions = ['delete_all_selected']

    @admin.action(description='🗑️ Supprimer tous les éléments sélectionnés')
    def delete_all_selected(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} évaluation(s) supprimée(s) avec succès.')

    fieldsets = (
        ('📋 Informations générales', {
            'fields': ('order', 'rating_type', 'score', 'is_anonymous')
        }),
        ('👥 Acteurs', {
            'fields': ('rater', 'rated_driver', 'rated_customer')
        }),
        ('⭐ Évaluation détaillée', {
            'fields': ('punctuality', 'driving_quality', 'vehicle_cleanliness', 'communication')
        }),
        ('💬 Feedback', {
            'fields': ('comment', 'tags')
        }),
        ('⏰ Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def order_link(self, obj):
        url = reverse('admin:order_order_change', args=[obj.order.pk])
        return format_html('<a href="{}">#{}</a>', url, str(obj.order.id)[:8])
    order_link.short_description = 'Commande'
    
    def score_stars(self, obj):
        stars = '⭐' * obj.score + '☆' * (5 - obj.score)
        return format_html('{} ({})', stars, obj.score)
    score_stars.short_description = 'Note'
    
    def rater_info(self, obj):
        if obj.rating_type == 'DRIVER_TO_CUSTOMER' and obj.rater:
            return f"🚗 {obj.rater}"
        elif obj.rating_type == 'CUSTOMER_TO_DRIVER':
            return f"👤 Client"
        return '-'
    rater_info.short_description = 'Évaluateur'
    
    def rated_info(self, obj):
        if obj.rating_type == 'DRIVER_TO_CUSTOMER' and obj.rated_customer:
            return f"👤 {obj.rated_customer}"
        elif obj.rating_type == 'CUSTOMER_TO_DRIVER' and obj.rated_driver:
            return f"🚗 {obj.rated_driver}"
        return '-'
    rated_info.short_description = 'Évalué'


@admin.register(TripTracking)
class TripTrackingAdmin(admin.ModelAdmin):
    list_display = [
        'order_link', 'driver', 'coordinates', 'speed_kmh',
        'order_status', 'recorded_at'
    ]
    list_filter = ['order_status', 'recorded_at', 'driver']
    search_fields = ['order__id', 'driver__name', 'driver__surname']
    readonly_fields = ['recorded_at']
    date_hierarchy = 'recorded_at'
    actions = ['delete_all_selected']

    @admin.action(description='🗑️ Supprimer tous les éléments sélectionnés')
    def delete_all_selected(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} suivi(s) de trajet supprimé(s) avec succès.')

    fieldsets = (
        ('📋 Informations', {
            'fields': ('order', 'driver', 'order_status')
        }),
        ('📍 Position GPS', {
            'fields': (
                ('latitude', 'longitude'),
                ('speed_kmh', 'heading', 'accuracy')
            )
        }),
        ('⏰ Timestamp', {
            'fields': ('recorded_at',)
        })
    )
    
    def order_link(self, obj):
        url = reverse('admin:order_order_change', args=[obj.order.pk])
        return format_html('<a href="{}">#{}</a>', url, str(obj.order.id)[:8])
    order_link.short_description = 'Commande'
    
    def coordinates(self, obj):
        return format_html(
            '<a href="https://maps.google.com/?q={},{}" target="_blank">📍 {}, {}</a>',
            obj.latitude, obj.longitude, 
            round(float(obj.latitude), 6), round(float(obj.longitude), 6)
        )
    coordinates.short_description = 'Coordonnées'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'driver')


@admin.register(DriverPool)
class DriverPoolAdmin(admin.ModelAdmin):
    list_display = [
        'order_link', 'driver', 'priority_badge', 'distance_km',
        'status_badge', 'response_time', 'requested_at'
    ]
    list_filter = ['request_status', 'priority_order', 'requested_at']
    search_fields = [
        'order__id', 'driver__name', 'driver__surname',
        'driver__phone_number'
    ]
    readonly_fields = ['requested_at', 'responded_at', 'response_time_seconds']
    actions = ['delete_all_selected']

    @admin.action(description='🗑️ Supprimer tous les éléments sélectionnés')
    def delete_all_selected(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} requête(s) de chauffeur supprimée(s) avec succès.')

    fieldsets = (
        ('📋 Informations', {
            'fields': ('order', 'driver', 'priority_order', 'distance_km')
        }),
        ('📊 Statut', {
            'fields': ('request_status', 'rejection_reason')
        }),
        ('⏰ Timing', {
            'fields': (
                'requested_at', 'responded_at', 'timeout_at',
                'response_time_seconds'
            )
        })
    )
    
    def order_link(self, obj):
        url = reverse('admin:order_order_change', args=[obj.order.pk])
        return format_html('<a href="{}">#{}</a>', url, str(obj.order.id)[:8])
    order_link.short_description = 'Commande'
    
    def priority_badge(self, obj):
        colors = {1: 'green', 2: 'blue', 3: 'orange'}
        color = colors.get(obj.priority_order, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">#{}</span>',
            color, obj.priority_order
        )
    priority_badge.short_description = 'Priorité'
    
    def status_badge(self, obj):
        colors = {
            'PENDING': 'orange',
            'ACCEPTED': 'green',
            'REJECTED': 'red',
            'TIMEOUT': 'gray',
            'CANCELLED': 'darkred',
        }
        color = colors.get(obj.request_status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_request_status_display()
        )
    status_badge.short_description = 'Statut'
    
    def response_time(self, obj):
        if obj.response_time_seconds:
            return f"{obj.response_time_seconds}s"
        return '-'
    response_time.short_description = 'Temps réponse'


@admin.register(DriverStatus)
class DriverStatusAdmin(admin.ModelAdmin):
    list_display = [
        'driver', 'status_badge', 'location_link', 'orders_today',
        'earnings_today', 'last_location_update', 'last_online'
    ]
    list_filter = ['status', 'last_online', 'updated_at']
    search_fields = [
        'driver__name', 'driver__surname', 'driver__phone_number'
    ]
    readonly_fields = [
        'last_location_update', 'last_online', 'updated_at',
        'session_started_at'
    ]
    
    fieldsets = (
        ('👤 Chauffeur', {
            'fields': ('driver', 'status')
        }),
        ('📍 Position actuelle', {
            'fields': (
                ('current_latitude', 'current_longitude'),
                'last_location_update'
            )
        }),
        ('📊 Statistiques du jour', {
            'fields': (
                'total_orders_today', 'total_earnings_today',
                'session_started_at'
            )
        }),
        ('🔌 WebSocket', {
            'fields': ('websocket_channel',)
        }),
        ('⏰ Timestamps', {
            'fields': ('last_online', 'updated_at')
        })
    )
    
    actions = ['set_online', 'set_offline', 'reset_daily_stats', 'delete_all_selected']

    @admin.action(description='🗑️ Supprimer tous les éléments sélectionnés')
    def delete_all_selected(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} statut(s) de chauffeur supprimé(s) avec succès.')

    def status_badge(self, obj):
        colors = {
            'OFFLINE': 'gray',
            'ONLINE': 'green',
            'BUSY': 'orange',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Statut'
    
    def location_link(self, obj):
        if obj.current_latitude and obj.current_longitude:
            return format_html(
                '<a href="https://maps.google.com/?q={},{}" target="_blank">📍 Voir sur la carte</a>',
                obj.current_latitude, obj.current_longitude
            )
        return '📍 Position inconnue'
    location_link.short_description = 'Position'
    
    def orders_today(self, obj):
        return format_html('<strong>{}</strong>', obj.total_orders_today)
    orders_today.short_description = 'Commandes'
    
    def earnings_today(self, obj):
        return format_html('<strong>{} FCFA</strong>', obj.total_earnings_today)
    earnings_today.short_description = 'Gains'
    
    def set_online(self, request, queryset):
        for status in queryset:
            status.go_online()
        self.message_user(request, f"{queryset.count()} chauffeur(s) mis en ligne")
    set_online.short_description = "Mettre en ligne"
    
    def set_offline(self, request, queryset):
        for status in queryset:
            status.go_offline()
        self.message_user(request, f"{queryset.count()} chauffeur(s) mis hors ligne")
    set_offline.short_description = "Mettre hors ligne"
    
    def reset_daily_stats(self, request, queryset):
        queryset.update(total_orders_today=0, total_earnings_today=0)
        self.message_user(request, f"Statistiques réinitialisées pour {queryset.count()} chauffeur(s)")
    reset_daily_stats.short_description = "Réinitialiser stats du jour"


@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    list_display = [
        'order_link', 'event_badge', 'actor', 'location',
        'created_at'
    ]
    list_filter = ['event_type', 'created_at']
    search_fields = [
        'order__id', 'driver__name', 'customer__name',
        'notes'
    ]
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    actions = ['delete_all_selected']

    @admin.action(description='🗑️ Supprimer tous les éléments sélectionnés')
    def delete_all_selected(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} événement(s) de suivi supprimé(s) avec succès.')

    fieldsets = (
        ('📋 Événement', {
            'fields': ('order', 'event_type')
        }),
        ('👥 Acteurs', {
            'fields': ('driver', 'customer')
        }),
        ('📍 Position', {
            'fields': (('latitude', 'longitude'),)
        }),
        ('📝 Détails', {
            'fields': ('notes', 'metadata')
        }),
        ('⏰ Timestamp', {
            'fields': ('created_at',)
        })
    )
    
    def order_link(self, obj):
        url = reverse('admin:order_order_change', args=[obj.order.pk])
        return format_html('<a href="{}">#{}</a>', url, str(obj.order.id)[:8])
    order_link.short_description = 'Commande'
    
    def event_badge(self, obj):
        colors = {
            'ORDER_CREATED': 'blue',
            'DRIVER_ACCEPTED': 'green',
            'DRIVER_REJECTED': 'red',
            'TRIP_STARTED': 'cyan',
            'TRIP_COMPLETED': 'green',
            'ORDER_CANCELLED': 'red',
            'PAYMENT_COMPLETED': 'green',
            'PAYMENT_FAILED': 'red',
        }
        color = colors.get(obj.event_type, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_event_type_display()
        )
    event_badge.short_description = 'Événement'
    
    def actor(self, obj):
        if obj.driver:
            return f"🚗 {obj.driver}"
        elif obj.customer:
            return f"👤 {obj.customer}"
        return '-'
    actor.short_description = 'Acteur'
    
    def location(self, obj):
        if obj.latitude and obj.longitude:
            return format_html('📍 {}, {}', 
                             round(float(obj.latitude), 6), 
                             round(float(obj.longitude), 6))
        return '-'
    location.short_description = 'Position'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'order', 'driver', 'customer'
        )


@admin.register(CustomerStatus)
class CustomerStatusAdmin(admin.ModelAdmin):
    list_display = [
        'customer', 'location_link', 'current_order_link',
        'last_location_update', 'updated_at'
    ]
    list_filter = ['last_location_update', 'updated_at']
    search_fields = [
        'customer__name', 'customer__surname', 'customer__phone_number'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'last_location_update'
    ]
    actions = ['delete_all_selected']

    @admin.action(description='🗑️ Supprimer tous les éléments sélectionnés')
    def delete_all_selected(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} statut(s) de client supprimé(s) avec succès.')

    fieldsets = (
        ('👤 Client', {
            'fields': ('customer',)
        }),
        ('📍 Position actuelle', {
            'fields': (
                ('current_latitude', 'current_longitude'),
                'last_location_update'
            )
        }),
        ('📋 Commande active', {
            'fields': ('current_order',)
        }),
        ('🔌 WebSocket', {
            'fields': ('websocket_channel',)
        }),
        ('⏰ Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    def location_link(self, obj):
        if obj.current_latitude and obj.current_longitude:
            return format_html(
                '<a href="https://maps.google.com/?q={},{}" target="_blank">📍 Voir sur la carte</a>',
                obj.current_latitude, obj.current_longitude
            )
        return '📍 Position inconnue'
    location_link.short_description = 'Position'
    
    def current_order_link(self, obj):
        if obj.current_order:
            url = reverse('admin:order_order_change', args=[obj.current_order.pk])
            return format_html('<a href="{}">🚗 #{}</a>', url, str(obj.current_order.id)[:8])
        return '🚗 Aucune commande active'
    current_order_link.short_description = 'Commande active'
