from decimal import Decimal
from datetime import datetime, time
from django.utils import timezone
from api.models import GeneralConfig, VehicleType, City, VipZone, VipZoneKilometerRule
from .models import Order, DriverStatus


class PricingService:
    """Service pour calculer les prix des commandes"""
    
    def calculate_order_price(self, vehicle_type_id, city_id, distance_km, vip_zone_id=None, is_night=False):
        """
        Calcule le prix total d'une commande
        """
        # Prix de base de la course
        base_price = self._get_config_value('STD_PRICELIST_ORDER', 500)
        
        # Prix par kilomètre
        price_per_km = self._get_config_value('PRICE_PER_KM', 250)
        distance_price = Decimal(str(distance_km)) * Decimal(str(price_per_km))
        
        # Prix additionnel du type de véhicule
        vehicle_additional_price = self._get_vehicle_additional_price(vehicle_type_id)
        
        # Prix de la ville (jour/nuit)
        city_price = self._get_city_price(city_id, is_night)
        
        # Prix zone VIP si applicable
        vip_zone_price = Decimal('0')
        if vip_zone_id:
            vip_zone_price = self._get_vip_zone_price(vip_zone_id, distance_km, is_night)
        
        # Total
        total_price = (
            Decimal(str(base_price)) + 
            distance_price + 
            vehicle_additional_price + 
            city_price + 
            vip_zone_price
        )
        
        return {
            'base_price': Decimal(str(base_price)),
            'distance_price': distance_price,
            'vehicle_additional_price': vehicle_additional_price,
            'city_price': city_price,
            'vip_zone_price': vip_zone_price,
            'total_price': total_price,
            'is_night_fare': is_night
        }
    
    def _get_config_value(self, search_key, default_value):
        """Récupère une valeur de configuration"""
        try:
            config = GeneralConfig.objects.get(search_key=search_key, active=True)
            return config.get_numeric_value() or default_value
        except GeneralConfig.DoesNotExist:
            return default_value
    
    def _get_vehicle_additional_price(self, vehicle_type_id):
        """Récupère le prix additionnel du type de véhicule"""
        try:
            vehicle_type = VehicleType.objects.get(id=vehicle_type_id, is_active=True)
            return vehicle_type.additional_amount
        except VehicleType.DoesNotExist:
            return Decimal('0')
    
    def _get_city_price(self, city_id, is_night):
        """Récupère le prix de la ville selon l'heure"""
        try:
            city = City.objects.get(id=city_id, active=True)
            return city.prix_nuit if is_night else city.prix_jour
        except City.DoesNotExist:
            return Decimal('0')
    
    def _get_vip_zone_price(self, vip_zone_id, distance_km, is_night):
        """Calcule le prix pour une zone VIP avec les règles kilométriques"""
        try:
            vip_zone = VipZone.objects.get(id=vip_zone_id, active=True)
            
            # Prix de base de la zone VIP
            base_vip_price = vip_zone.prix_nuit if is_night else vip_zone.prix_jour
            
            # Chercher la règle kilométrique applicable
            rules = VipZoneKilometerRule.objects.filter(
                vip_zone=vip_zone,
                min_kilometers__lte=distance_km,
                active=True
            ).order_by('-min_kilometers')
            
            if rules.exists():
                rule = rules.first()
                km_price = rule.prix_nuit_per_km if is_night else rule.prix_jour_per_km
                additional_km_price = Decimal(str(distance_km)) * km_price
                return base_vip_price + additional_km_price
            else:
                return base_vip_price
                
        except VipZone.DoesNotExist:
            return Decimal('0')
    
    def is_night_time(self, current_time=None):
        """Détermine si c'est l'heure de nuit (ex: 22h-6h)"""
        if current_time is None:
            current_time = timezone.now().time()
        
        night_start = time(22, 0)  # 22h00
        night_end = time(6, 0)     # 06h00
        
        if night_start <= current_time or current_time <= night_end:
            return True
        return False


class OrderService:
    """Service pour gérer les commandes et le matching"""
    
    def __init__(self):
        self.pricing_service = PricingService()
    
    def find_nearby_drivers(self, pickup_lat, pickup_lng, radius_km=5):
        """
        Trouve les chauffeurs disponibles dans un rayon donné
        """
        # Conversion approximative: 1 degré ≈ 111km
        lat_delta = radius_km / 111.0
        lng_delta = radius_km / (111.0 * abs(pickup_lat))
        
        nearby_drivers = DriverStatus.objects.filter(
            status='ONLINE',
            current_latitude__isnull=False,
            current_longitude__isnull=False,
            current_latitude__range=(pickup_lat - lat_delta, pickup_lat + lat_delta),
            current_longitude__range=(pickup_lng - lng_delta, pickup_lng + lng_delta)
        ).select_related('driver')
        
        return nearby_drivers
    
    def calculate_distance(self, lat1, lng1, lat2, lng2):
        """
        Calcule la distance approximative entre deux points (formule de Haversine simplifiée)
        """
        from math import radians, cos, sin, asin, sqrt
        
        # Convertir en radians
        lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
        
        # Formule de Haversine
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
        c = 2 * asin(sqrt(a))
        
        # Rayon de la Terre en km
        earth_radius = 6371
        
        return earth_radius * c
    
    def get_order_status_flow(self):
        """Retourne les transitions de statut possibles"""
        return {
            'PENDING': ['ACCEPTED', 'CANCELLED'],
            'ACCEPTED': ['IN_PROGRESS', 'CANCELLED'],
            'IN_PROGRESS': ['COMPLETED'],
            'COMPLETED': [],
            'CANCELLED': []
        }
    
    def can_transition_status(self, current_status, new_status):
        """Vérifie si une transition de statut est valide"""
        flow = self.get_order_status_flow()
        return new_status in flow.get(current_status, [])
    
    def get_waiting_time_limit(self):
        """Récupère le temps d'attente maximum d'une commande"""
        try:
            config = GeneralConfig.objects.get(search_key='MAX_WAITING_TIME', active=True)
            return int(config.valeur)
        except (GeneralConfig.DoesNotExist, ValueError):
            return 60  # 60 secondes par défaut


class NotificationService:
    """Service pour gérer les notifications en temps réel"""
    
    def __init__(self, channel_layer):
        self.channel_layer = channel_layer
    
    async def notify_customer_order_accepted(self, customer_id, order_id, driver_info):
        """Notifie le client que sa commande a été acceptée"""
        await self.channel_layer.group_send(
            f'customer_{customer_id}',
            {
                'type': 'order_accepted',
                'order_id': order_id,
                'driver_info': driver_info
            }
        )
    
    async def notify_customer_trip_started(self, customer_id, order_id):
        """Notifie le client que la course a commencé"""
        await self.channel_layer.group_send(
            f'customer_{customer_id}',
            {
                'type': 'trip_started',
                'order_id': order_id
            }
        )
    
    async def notify_customer_trip_completed(self, customer_id, order_id):
        """Notifie le client que la course est terminée"""
        await self.channel_layer.group_send(
            f'customer_{customer_id}',
            {
                'type': 'trip_completed',
                'order_id': order_id
            }
        )
    
    async def notify_driver_location_to_customer(self, customer_id, order_id, latitude, longitude):
        """Envoie la position du chauffeur au client"""
        await self.channel_layer.group_send(
            f'customer_{customer_id}',
            {
                'type': 'driver_location_update',
                'order_id': order_id,
                'latitude': latitude,
                'longitude': longitude
            }
        )
    
    async def notify_drivers_new_order(self, driver_ids, order_data):
        """Notifie les chauffeurs disponibles d'une nouvelle commande"""
        for driver_id in driver_ids:
            await self.channel_layer.group_send(
                f'driver_{driver_id}',
                {
                    'type': 'order_request',
                    'order_data': order_data
                }
            )