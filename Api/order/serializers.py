"""
Serializers pour le module de commande VTC
"""
from rest_framework import serializers
from django.db import transaction
from decimal import Decimal

from users.models import UserDriver, UserCustomer
from vehicles.models import VehicleType
from core.models import City, VipZone
from .models import (
    Order, DriverStatus, CustomerStatus, OrderTracking, PaymentMethod,
    Rating, TripTracking, DriverPool
)


# ============= PAYMENT SERIALIZERS =============

class PaymentMethodSerializer(serializers.ModelSerializer):
    """Serializer pour les méthodes de paiement"""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'type', 'type_display', 'name', 'description',
            'icon', 'is_active', 'min_amount', 'max_amount'
        ]


# ============= DRIVER STATUS SERIALIZERS =============

class DriverStatusSerializer(serializers.ModelSerializer):
    """Serializer pour le statut du chauffeur"""
    driver_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = DriverStatus
        fields = [
            'id', 'driver', 'driver_name', 'status', 'status_display',
            'current_latitude', 'current_longitude', 'last_location_update',
            'last_online', 'total_orders_today', 'total_earnings_today',
            'session_started_at', 'updated_at'
        ]
        read_only_fields = ['id', 'driver', 'updated_at']
    
    def get_driver_name(self, obj):
        return f"{obj.driver.name} {obj.driver.surname}"


class CustomerStatusSerializer(serializers.ModelSerializer):
    """Serializer pour le statut du client"""
    customer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomerStatus
        fields = [
            'id', 'customer', 'customer_name',
            'current_latitude', 'current_longitude', 'last_location_update',
            'current_order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'customer', 'created_at', 'updated_at']
    
    def get_customer_name(self, obj):
        return f"Client {obj.customer.phone_number}"


class UpdateLocationSerializer(serializers.Serializer):
    """Serializer pour la mise à jour de position GPS"""
    latitude = serializers.DecimalField(max_digits=10, decimal_places=8)
    longitude = serializers.DecimalField(max_digits=11, decimal_places=8)
    speed_kmh = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, allow_null=True
    )
    heading = serializers.IntegerField(
        min_value=0, max_value=359, required=False, allow_null=True
    )
    accuracy = serializers.DecimalField(
        max_digits=6, decimal_places=2, required=False, allow_null=True
    )


# ============= ORDER SERIALIZERS =============

class OrderSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour une commande"""
    customer_name = serializers.SerializerMethodField()
    driver_name = serializers.SerializerMethodField()
    vehicle_type_name = serializers.CharField(source='vehicle_type.name', read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)
    vip_zone_name = serializers.CharField(source='vip_zone.name', read_only=True, allow_null=True)
    payment_method_name = serializers.CharField(source='payment_method.name', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'customer', 'customer_name', 'driver', 'driver_name',
            'pickup_address', 'pickup_latitude', 'pickup_longitude',
            'destination_address', 'destination_latitude', 'destination_longitude',
            'vehicle_type', 'vehicle_type_name', 'city', 'city_name',
            'vip_zone', 'vip_zone_name', 'payment_method', 'payment_method_name',
            'payment_status', 'payment_status_display',
            'estimated_distance_km', 'actual_distance_km',
            'base_price', 'distance_price', 'vehicle_additional_price',
            'city_price', 'vip_zone_price', 'waiting_price',
            'total_price', 'final_price', 'waiting_time',
            'driver_rating', 'customer_rating',
            'is_night_fare', 'status', 'status_display',
            'customer_notes', 'driver_notes', 'cancellation_reason',
            'created_at', 'accepted_at', 'driver_arrived_at',
            'started_at', 'completed_at', 'cancelled_at', 'paid_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_customer_name(self, obj):
        return f"Client {obj.customer.phone_number}" if obj.customer else None
    
    def get_driver_name(self, obj):
        return f"{obj.driver.name} {obj.driver.surname}" if obj.driver else None


class OrderListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour les listes de commandes"""
    customer_name = serializers.SerializerMethodField()
    driver_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration_minutes = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'customer_name', 'driver_name', 'pickup_address',
            'destination_address', 'total_price', 'final_price',
            'status', 'status_display', 'created_at',
            'duration_minutes', 'driver_rating', 'customer_rating'
        ]
    
    def get_customer_name(self, obj):
        return f"Client {obj.customer.phone_number}" if obj.customer else None
    
    def get_driver_name(self, obj):
        return f"{obj.driver.name} {obj.driver.surname}" if obj.driver else None
    
    def get_duration_minutes(self, obj):
        if obj.started_at and obj.completed_at:
            duration = obj.completed_at - obj.started_at
            return int(duration.total_seconds() / 60)
        return None


class SearchDriversSerializer(serializers.Serializer):
    """Serializer pour la recherche de chauffeurs"""
    pickup_latitude = serializers.DecimalField(max_digits=10, decimal_places=8)
    pickup_longitude = serializers.DecimalField(max_digits=11, decimal_places=8)
    vehicle_type_id = serializers.IntegerField(required=False, allow_null=True)
    radius_km = serializers.FloatField(default=5.0, min_value=0.5, max_value=50)


class EstimatePriceSerializer(serializers.Serializer):
    """Serializer pour l'estimation de prix"""
    pickup_latitude = serializers.DecimalField(max_digits=10, decimal_places=8)
    pickup_longitude = serializers.DecimalField(max_digits=11, decimal_places=8)
    destination_latitude = serializers.DecimalField(max_digits=10, decimal_places=8)
    destination_longitude = serializers.DecimalField(max_digits=11, decimal_places=8)
    vehicle_type_id = serializers.IntegerField()
    city_id = serializers.IntegerField()
    vip_zone_id = serializers.IntegerField(required=False, allow_null=True)
    
    def validate_vehicle_type_id(self, value):
        if not VehicleType.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Type de véhicule invalide ou inactif")
        return value
    
    def validate_city_id(self, value):
        if not City.objects.filter(id=value, active=True).exists():
            raise serializers.ValidationError("Ville invalide ou inactive")
        return value
    
    def validate_vip_zone_id(self, value):
        if value and not VipZone.objects.filter(id=value, active=True).exists():
            raise serializers.ValidationError("Zone VIP invalide ou inactive")
        return value


class CreateOrderSerializer(serializers.Serializer):
    """Serializer pour la création d'une commande"""
    pickup_address = serializers.CharField(max_length=500)
    pickup_latitude = serializers.DecimalField(max_digits=10, decimal_places=8)
    pickup_longitude = serializers.DecimalField(max_digits=11, decimal_places=8)
    destination_address = serializers.CharField(max_length=500)
    destination_latitude = serializers.DecimalField(max_digits=10, decimal_places=8)
    destination_longitude = serializers.DecimalField(max_digits=11, decimal_places=8)
    vehicle_type_id = serializers.IntegerField()
    city_id = serializers.IntegerField()
    vip_zone_id = serializers.IntegerField(required=False, allow_null=True)
    payment_method_id = serializers.IntegerField(required=False, allow_null=True)
    customer_notes = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    
    def validate_vehicle_type_id(self, value):
        if not VehicleType.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Type de véhicule invalide ou inactif")
        return value
    
    def validate_city_id(self, value):
        if not City.objects.filter(id=value, active=True).exists():
            raise serializers.ValidationError("Ville invalide ou inactive")
        return value
    
    def validate_vip_zone_id(self, value):
        if value and not VipZone.objects.filter(id=value, active=True).exists():
            raise serializers.ValidationError("Zone VIP invalide ou inactive")
        return value
    
    def validate_payment_method_id(self, value):
        if value and not PaymentMethod.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Méthode de paiement invalide ou inactive")
        return value
    
    def validate(self, data):
        """Validation globale"""
        # Vérifier que les coordonnées sont différentes
        if (data['pickup_latitude'] == data['destination_latitude'] and 
            data['pickup_longitude'] == data['destination_longitude']):
            raise serializers.ValidationError(
                "Les adresses de départ et d'arrivée doivent être différentes"
            )
        
        # Vérifier la distance maximale
        from .services import OrderService
        service = OrderService()
        distance = service.calculate_real_distance(
            float(data['pickup_latitude']),
            float(data['pickup_longitude']),
            float(data['destination_latitude']),
            float(data['destination_longitude'])
        )
        
        if distance > 100:  # 100 km max
            raise serializers.ValidationError(
                "La distance est trop importante (maximum 100 km)"
            )
        
        return data


class CancelOrderSerializer(serializers.Serializer):
    """Serializer pour l'annulation d'une commande"""
    reason = serializers.CharField(max_length=500, required=True)


class CompleteOrderSerializer(serializers.Serializer):
    """Serializer pour terminer une course"""
    actual_distance_km = serializers.DecimalField(
        max_digits=8, decimal_places=2, min_value=0
    )
    waiting_time = serializers.IntegerField(min_value=0, default=0)
    driver_notes = serializers.CharField(
        max_length=1000, required=False, allow_blank=True
    )


# ============= RATING SERIALIZERS =============

class RatingSerializer(serializers.ModelSerializer):
    """Serializer pour l'affichage des notations"""
    rater_name = serializers.SerializerMethodField()
    rated_name = serializers.SerializerMethodField()
    rating_type_display = serializers.CharField(source='get_rating_type_display', read_only=True)
    
    class Meta:
        model = Rating
        fields = [
            'id', 'order', 'rating_type', 'rating_type_display',
            'rater', 'rater_name', 'rated_driver', 'rated_customer', 'rated_name',
            'score', 'comment', 'punctuality', 'driving_quality',
            'vehicle_cleanliness', 'communication', 'tags',
            'is_anonymous', 'created_at'
        ]
    
    def get_rater_name(self, obj):
        if obj.is_anonymous:
            return "Anonyme"
        if obj.rater:
            return f"{obj.rater.name} {obj.rater.surname}"
        return "Client"
    
    def get_rated_name(self, obj):
        if obj.rated_driver:
            return f"{obj.rated_driver.name} {obj.rated_driver.surname}"
        elif obj.rated_customer:
            return f"Client {obj.rated_customer.phone_number}"
        return None


class CreateRatingSerializer(serializers.Serializer):
    """Serializer pour créer une notation"""
    score = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    punctuality = serializers.IntegerField(min_value=1, max_value=5, required=False)
    driving_quality = serializers.IntegerField(min_value=1, max_value=5, required=False)
    vehicle_cleanliness = serializers.IntegerField(min_value=1, max_value=5, required=False)
    communication = serializers.IntegerField(min_value=1, max_value=5, required=False)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        default=list
    )
    is_anonymous = serializers.BooleanField(default=False)


# ============= TRACKING SERIALIZERS =============

class TripTrackingSerializer(serializers.ModelSerializer):
    """Serializer pour le tracking GPS"""
    
    class Meta:
        model = TripTracking
        fields = [
            'id', 'latitude', 'longitude', 'speed_kmh',
            'heading', 'accuracy', 'order_status', 'recorded_at'
        ]


class OrderTrackingSerializer(serializers.ModelSerializer):
    """Serializer pour les événements de tracking"""
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    driver_name = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderTracking
        fields = [
            'id', 'event_type', 'event_type_display',
            'driver', 'driver_name', 'customer', 'customer_name',
            'latitude', 'longitude', 'metadata', 'notes', 'created_at'
        ]
    
    def get_driver_name(self, obj):
        return f"{obj.driver.name} {obj.driver.surname}" if obj.driver else None
    
    def get_customer_name(self, obj):
        return f"Client {obj.customer.phone_number}" if obj.customer else None


# ============= DRIVER POOL SERIALIZERS =============

class DriverPoolSerializer(serializers.ModelSerializer):
    """Serializer pour le pool de chauffeurs"""
    driver_name = serializers.SerializerMethodField()
    request_status_display = serializers.CharField(source='get_request_status_display', read_only=True)
    
    class Meta:
        model = DriverPool
        fields = [
            'id', 'order', 'driver', 'driver_name', 'priority_order',
            'distance_km', 'request_status', 'request_status_display',
            'requested_at', 'responded_at', 'timeout_at',
            'response_time_seconds', 'rejection_reason'
        ]
    
    def get_driver_name(self, obj):
        return f"{obj.driver.name} {obj.driver.surname}" if obj.driver else None


# ============= PROCESS PAYMENT SERIALIZER =============

class ProcessPaymentSerializer(serializers.Serializer):
    """Serializer pour traiter un paiement"""
    payment_method_id = serializers.IntegerField(required=False)
    transaction_reference = serializers.CharField(max_length=255, required=False)
    
    def validate_payment_method_id(self, value):
        if value and not PaymentMethod.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Méthode de paiement invalide ou inactive")
        return value
