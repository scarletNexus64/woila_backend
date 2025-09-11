"""
Services métier pour la gestion des commandes VTC
"""
from decimal import Decimal
from datetime import datetime, time, timedelta
from typing import List, Dict, Optional, Tuple
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, F, Avg, Count
from django.conf import settings
import logging
import math

from api.models import (
    GeneralConfig, VehicleType, City, VipZone, 
    VipZoneKilometerRule, UserDriver, UserCustomer, Vehicle
)
from .models import (
    Order, DriverStatus, PaymentMethod, Rating, 
    TripTracking, DriverPool, OrderTracking
)

logger = logging.getLogger(__name__)


class PricingService:
    """Service pour calculer les prix des commandes"""
    
    def calculate_order_price(self, vehicle_type_id, city_id, distance_km, 
                            vip_zone_id=None, is_night=None, waiting_minutes=0):
        """
        Calcule le prix total d'une commande avec tous les paramètres
        """
        if is_night is None:
            is_night = self.is_night_time()
        
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
        
        # Prix d'attente
        waiting_price = self.calculate_waiting_price(waiting_minutes)
        
        # Total
        total_price = (
            Decimal(str(base_price)) + 
            distance_price + 
            vehicle_additional_price + 
            city_price + 
            vip_zone_price +
            waiting_price
        )
        
        # Retourner les valeurs Decimal pour utilisation interne
        # Les vues/serializers doivent convertir en float pour JSON
        return {
            'base_price': Decimal(str(base_price)),
            'distance_price': distance_price,
            'vehicle_additional_price': vehicle_additional_price,
            'city_price': city_price,
            'vip_zone_price': vip_zone_price,
            'waiting_price': waiting_price,
            'total_price': total_price,
            'is_night_fare': is_night,
            'breakdown': {
                'base': float(base_price),
                'per_km': float(price_per_km),
                'distance_km': float(distance_km),
                'waiting_minutes': waiting_minutes
            }
        }
    
    def calculate_waiting_price(self, waiting_minutes):
        """Calcule le prix basé sur le temps d'attente"""
        if waiting_minutes <= 0:
            return Decimal('0')
        
        price_per_minute = self._get_config_value('PRICE_PER_WAITING_MINUTE', 50)
        free_waiting_time = self._get_config_value('FREE_WAITING_TIME', 5)
        
        # Les premières minutes sont gratuites
        billable_minutes = max(0, waiting_minutes - free_waiting_time)
        return Decimal(str(billable_minutes)) * Decimal(str(price_per_minute))
    
    def update_final_price(self, order: Order) -> Decimal:
        """
        Met à jour le prix final d'une commande basé sur la distance réelle
        et le temps d'attente
        """
        if not order.actual_distance_km:
            logger.warning(f"Pas de distance réelle pour la commande {order.id}")
            return order.total_price
        
        # Recalculer avec la distance réelle
        pricing = self.calculate_order_price(
            vehicle_type_id=order.vehicle_type_id,
            city_id=order.city_id,
            distance_km=float(order.actual_distance_km),
            vip_zone_id=order.vip_zone_id if order.vip_zone else None,
            is_night=order.is_night_fare,
            waiting_minutes=order.waiting_time or 0
        )
        
        order.final_price = pricing['total_price']
        order.waiting_price = pricing['waiting_price']
        order.distance_price = pricing['distance_price']
        order.save(update_fields=['final_price', 'waiting_price', 'distance_price'])
        
        logger.info(f"Prix final mis à jour pour commande {order.id}: {order.final_price}")
        return order.final_price
    
    def estimate_price_range(self, vehicle_type_id, city_id, estimated_distance_km, 
                           vip_zone_id=None) -> Dict:
        """
        Estime une fourchette de prix (min/max) pour une course
        """
        is_night = self.is_night_time()
        
        # Prix minimum (sans attente, distance optimale -10%)
        min_distance = estimated_distance_km * 0.9
        min_price = self.calculate_order_price(
            vehicle_type_id=vehicle_type_id,
            city_id=city_id,
            distance_km=min_distance,
            vip_zone_id=vip_zone_id,
            is_night=is_night,
            waiting_minutes=0
        )
        
        # Prix maximum (avec attente moyenne, distance +20%)
        max_distance = estimated_distance_km * 1.2
        avg_waiting = self._get_config_value('AVG_WAITING_TIME', 10)
        max_price = self.calculate_order_price(
            vehicle_type_id=vehicle_type_id,
            city_id=city_id,
            distance_km=max_distance,
            vip_zone_id=vip_zone_id,
            is_night=is_night,
            waiting_minutes=avg_waiting
        )
        
        return {
            'min_price': float(min_price['total_price']),
            'max_price': float(max_price['total_price']),
            'estimated_price': float((min_price['total_price'] + max_price['total_price']) / 2),
            'is_night_fare': is_night,
            'currency': 'FCFA'
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
        """Détermine si c'est l'heure de nuit"""
        if current_time is None:
            current_time = timezone.now().time()
        
        night_start_hour = self._get_config_value('NIGHT_FARE_START_HOUR', 22)
        night_end_hour = self._get_config_value('NIGHT_FARE_END_HOUR', 6)
        
        night_start = time(int(night_start_hour), 0)
        night_end = time(int(night_end_hour), 0)
        
        if night_start <= current_time or current_time <= night_end:
            return True
        return False


class OrderService:
    """Service amélioré pour gérer les commandes et le matching"""
    
    def __init__(self):
        self.pricing_service = PricingService()
    
    def find_nearby_drivers(self, pickup_lat, pickup_lng, vehicle_type_id=None, 
                           radius_km=None, limit=20) -> List[Dict]:
        """
        Trouve les chauffeurs disponibles basé sur leur position GPS réelle
        """
        drivers_with_distance = []
        radius_km = radius_km or 10  # Rayon par défaut de 10 km
        
        # Récupérer les chauffeurs ONLINE avec position GPS disponible
        query = DriverStatus.objects.filter(
            status='ONLINE',
            current_latitude__isnull=False,
            current_longitude__isnull=False
        ).select_related('driver')
        
        # Si un type de véhicule est spécifié, filtrer
        if vehicle_type_id:
            query = query.filter(
                driver__vehicles__vehicle_type_id=vehicle_type_id,
                driver__vehicles__is_active=True,
                driver__vehicles__is_online=True
            ).distinct()
        
        for driver_status in query:
            # Calculer la distance réelle basée sur la position GPS
            distance = self.calculate_real_distance(
                pickup_lat, pickup_lng,
                float(driver_status.current_latitude),
                float(driver_status.current_longitude)
            )
            
            # Filtrer par rayon seulement si dans le rayon demandé
            if distance <= radius_km:
                driver_lat = float(driver_status.current_latitude)
                driver_lng = float(driver_status.current_longitude)
                
                # Récupérer les infos du véhicule
                vehicle = None
                if vehicle_type_id:
                    vehicle = Vehicle.objects.filter(
                        driver=driver_status.driver,
                        vehicle_type_id=vehicle_type_id,
                        is_active=True,
                        is_online=True
                    ).first()
                else:
                    vehicle = Vehicle.objects.filter(
                        driver=driver_status.driver,
                        is_active=True,
                        is_online=True
                    ).first()
                
                # Si le chauffeur a un véhicule actif, l'ajouter à la liste
                if vehicle:
                    # Calculer le rating moyen du chauffeur
                    avg_rating = Rating.objects.filter(
                        rated_driver=driver_status.driver,
                        rating_type='CUSTOMER_TO_DRIVER'
                    ).aggregate(avg=Avg('score'))['avg'] or 5.0
                    
                    drivers_with_distance.append({
                        'driver_id': driver_status.driver.id,
                        'driver_name': f"{driver_status.driver.name} {driver_status.driver.surname}",
                        'driver_phone': driver_status.driver.phone_number,
                        'distance_km': round(distance, 2),  # Distance GPS réelle
                        'latitude': driver_lat,
                        'longitude': driver_lng,
                        'vehicle': {
                            'id': vehicle.id,
                            'vehicle_type_id': vehicle.vehicle_type.id if vehicle.vehicle_type else None,
                            'type': vehicle.vehicle_type.name if vehicle.vehicle_type else None,
                            'plaque': vehicle.plaque_immatriculation,
                            'brand': vehicle.brand.name if vehicle.brand else None,
                            'model': vehicle.model.name if vehicle.model else None,
                            'color': vehicle.color.name if vehicle.color else None,
                        },
                        'rating': round(avg_rating, 1),
                        'orders_today': driver_status.total_orders_today,
                        'last_update': driver_status.last_location_update.isoformat() if driver_status.last_location_update else None
                    })
                    
                    logger.info(f"📍 Chauffeur {driver_status.driver.id} trouvé à {round(distance, 2)}km de distance GPS réelle")
        
        # Trier par distance croissante (GPS réelle)
        drivers_with_distance.sort(key=lambda x: x['distance_km'])
        
        logger.info(f"🔍 Recherche GPS terminée: {len(drivers_with_distance)} chauffeurs trouvés dans un rayon de {radius_km}km")
        
        # Limiter le nombre de résultats
        return drivers_with_distance[:limit]
    
    def find_nearby_drivers_progressive(self, pickup_lat, pickup_lng, vehicle_type_id=None, 
                                       initial_radius_km=5, max_radius_km=50, step_km=5, 
                                       min_drivers=1) -> Dict:
        """
        Recherche progressive de chauffeurs : augmente le rayon progressivement jusqu'à trouver des chauffeurs
        Retourne les informations de recherche avec le rayon utilisé
        """
        current_radius = initial_radius_km
        drivers_found = []
        
        logger.info(f"🔍 Démarrage recherche progressive - Rayon initial: {initial_radius_km}km, Max: {max_radius_km}km")
        
        while current_radius <= max_radius_km and len(drivers_found) < min_drivers:
            logger.info(f"📏 Tentative de recherche avec rayon: {current_radius}km")
            
            # Rechercher les chauffeurs à ce rayon
            drivers_found = self.find_nearby_drivers(
                pickup_lat=pickup_lat,
                pickup_lng=pickup_lng,
                vehicle_type_id=vehicle_type_id,
                radius_km=current_radius
            )
            
            if len(drivers_found) >= min_drivers:
                logger.info(f"✅ Chauffeurs trouvés ! Rayon utilisé: {current_radius}km, Chauffeurs: {len(drivers_found)}")
                break
            
            logger.info(f"⚠️ Aucun chauffeur trouvé à {current_radius}km, élargissement...")
            current_radius += step_km
        
        # Obtenir les types de véhicules disponibles au rayon final
        vehicle_types = self.get_available_vehicle_types(
            pickup_lat=pickup_lat,
            pickup_lng=pickup_lng,
            radius_km=current_radius if drivers_found else max_radius_km
        )
        
        return {
            'drivers': drivers_found,
            'vehicle_types': vehicle_types,
            'radius_used_km': current_radius if drivers_found else max_radius_km,
            'search_attempted': True,
            'max_radius_reached': current_radius > max_radius_km
        }
    
    def calculate_real_distance(self, lat1: float, lng1: float, 
                               lat2: float, lng2: float) -> float:
        """
        Calcule la distance réelle entre deux points en utilisant geopy
        ou la formule de Haversine améliorée
        """
        try:
            # Essayer d'utiliser geopy si disponible
            from geopy.distance import geodesic
            point1 = (lat1, lng1)
            point2 = (lat2, lng2)
            return geodesic(point1, point2).km
        except ImportError:
            # Fallback sur Haversine
            return self._haversine_distance(lat1, lng1, lat2, lng2)
    
    def _haversine_distance(self, lat1: float, lng1: float, 
                           lat2: float, lng2: float) -> float:
        """
        Formule de Haversine pour calculer la distance entre deux points GPS
        """
        # Rayon de la Terre en km
        R = 6371.0
        
        # Convertir en radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        
        # Formule de Haversine
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(dlng / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def get_available_vehicle_types(self, pickup_lat: float, pickup_lng: float, 
                                   radius_km: float = None) -> List[Dict]:
        """
        Retourne les types de véhicules disponibles avec le nombre de chauffeurs
        """
        nearby_drivers = self.find_nearby_drivers(pickup_lat, pickup_lng, radius_km=radius_km)
        
        vehicle_types = {}
        for driver_info in nearby_drivers:
            if driver_info['vehicle'] and driver_info['vehicle']['vehicle_type_id']:
                vehicle_type_id = driver_info['vehicle']['vehicle_type_id']
                vehicle_type_name = driver_info['vehicle']['type']
                
                if vehicle_type_id not in vehicle_types:
                    vehicle_types[vehicle_type_id] = {
                        'vehicle_type_id': vehicle_type_id,
                        'type': vehicle_type_name,
                        'count': 0,
                        'nearest_distance': float('inf'),
                        'drivers': []
                    }
                
                vehicle_types[vehicle_type_id]['count'] += 1
                vehicle_types[vehicle_type_id]['nearest_distance'] = min(
                    vehicle_types[vehicle_type_id]['nearest_distance'],
                    driver_info['distance_km']
                )
                vehicle_types[vehicle_type_id]['drivers'].append(driver_info['driver_id'])
        
        return list(vehicle_types.values())
    
    @transaction.atomic
    def create_order(self, customer_id: int, order_data: Dict) -> Order:
        """
        Crée une nouvelle commande avec toutes les validations
        """
        customer = UserCustomer.objects.get(id=customer_id)
        
        # Calculer la distance estimée
        estimated_distance = self.calculate_real_distance(
            order_data['pickup_latitude'],
            order_data['pickup_longitude'],
            order_data['destination_latitude'],
            order_data['destination_longitude']
        )
        
        # Calculer le prix
        pricing = self.pricing_service.calculate_order_price(
            vehicle_type_id=order_data['vehicle_type_id'],
            city_id=order_data['city_id'],
            distance_km=estimated_distance,
            vip_zone_id=order_data.get('vip_zone_id'),
            is_night=None  # Auto-détecté
        )
        
        # Créer la commande
        order = Order.objects.create(
            customer=customer,
            pickup_address=order_data['pickup_address'],
            pickup_latitude=order_data['pickup_latitude'],
            pickup_longitude=order_data['pickup_longitude'],
            destination_address=order_data['destination_address'],
            destination_latitude=order_data['destination_latitude'],
            destination_longitude=order_data['destination_longitude'],
            vehicle_type_id=order_data['vehicle_type_id'],
            city_id=order_data['city_id'],
            vip_zone_id=order_data.get('vip_zone_id'),
            payment_method_id=order_data.get('payment_method_id'),
            estimated_distance_km=estimated_distance,
            base_price=pricing['base_price'],
            distance_price=pricing['distance_price'],
            vehicle_additional_price=pricing['vehicle_additional_price'],
            city_price=pricing['city_price'],
            vip_zone_price=pricing['vip_zone_price'],
            total_price=pricing['total_price'],
            is_night_fare=pricing['is_night_fare'],
            customer_notes=order_data.get('customer_notes', ''),
            status='PENDING'
        )
        
        # Créer l'événement de tracking
        # Convertir les Decimal en float pour la sérialisation JSON
        pricing_for_metadata = {
            'base_price': float(pricing['base_price']),
            'distance_price': float(pricing['distance_price']),
            'vehicle_additional_price': float(pricing['vehicle_additional_price']),
            'city_price': float(pricing['city_price']),
            'vip_zone_price': float(pricing['vip_zone_price']),
            'waiting_price': float(pricing['waiting_price']),
            'total_price': float(pricing['total_price']),
            'is_night_fare': pricing['is_night_fare'],
            'breakdown': pricing['breakdown']  # Déjà en float
        }
        
        OrderTracking.objects.create(
            order=order,
            event_type='ORDER_CREATED',
            customer=customer,
            latitude=order_data['pickup_latitude'],
            longitude=order_data['pickup_longitude'],
            metadata={'pricing': pricing_for_metadata}
        )
        
        logger.info(f"Commande {order.id} créée pour le client {customer_id}")
        return order
    
    def get_order_status_flow(self) -> Dict:
        """Retourne les transitions de statut possibles"""
        return {
            'DRAFT': ['PENDING', 'CANCELLED'],
            'PENDING': ['ACCEPTED', 'CANCELLED'],
            'ACCEPTED': ['DRIVER_ARRIVED', 'CANCELLED'],
            'DRIVER_ARRIVED': ['IN_PROGRESS', 'CANCELLED'],
            'IN_PROGRESS': ['COMPLETED'],
            'COMPLETED': [],
            'CANCELLED': []
        }
    
    def can_transition_status(self, current_status: str, new_status: str) -> bool:
        """Vérifie si une transition de statut est valide"""
        flow = self.get_order_status_flow()
        return new_status in flow.get(current_status, [])
    
    @transaction.atomic
    def update_order_status(self, order: Order, new_status: str, 
                           actor_driver: UserDriver = None,
                           actor_customer: UserCustomer = None,
                           notes: str = '') -> bool:
        """
        Met à jour le statut d'une commande avec validation et tracking
        """
        if not self.can_transition_status(order.status, new_status):
            logger.warning(f"Transition invalide: {order.status} → {new_status}")
            return False
        
        old_status = order.status
        order.status = new_status
        
        # Mettre à jour les timestamps appropriés
        now = timezone.now()
        if new_status == 'ACCEPTED':
            order.accepted_at = now
        elif new_status == 'DRIVER_ARRIVED':
            order.driver_arrived_at = now
        elif new_status == 'IN_PROGRESS':
            order.started_at = now
        elif new_status == 'COMPLETED':
            order.completed_at = now
        elif new_status == 'CANCELLED':
            order.cancelled_at = now
            order.cancellation_reason = notes
        
        order.save()
        
        # Créer l'événement de tracking
        event_type_map = {
            'ACCEPTED': 'DRIVER_ACCEPTED',
            'DRIVER_ARRIVED': 'DRIVER_ARRIVED',
            'IN_PROGRESS': 'TRIP_STARTED',
            'COMPLETED': 'TRIP_COMPLETED',
            'CANCELLED': 'ORDER_CANCELLED'
        }
        
        OrderTracking.objects.create(
            order=order,
            event_type=event_type_map.get(new_status, 'LOCATION_UPDATE'),
            driver=actor_driver,
            customer=actor_customer,
            notes=notes,
            metadata={'old_status': old_status, 'new_status': new_status}
        )
        
        logger.info(f"Commande {order.id}: {old_status} → {new_status}")
        return True
    
    def _get_config_value(self, search_key, default_value):
        """Helper pour récupérer une configuration"""
        try:
            config = GeneralConfig.objects.get(search_key=search_key, active=True)
            return config.get_numeric_value() or default_value
        except GeneralConfig.DoesNotExist:
            return default_value


class DriverPoolService:
    """Service pour gérer le pool de chauffeurs et l'attribution séquentielle"""
    
    def __init__(self):
        self.order_service = OrderService()
    
    @transaction.atomic
    def create_driver_pool(self, order: Order, max_drivers: int = 10) -> List[DriverPool]:
        """
        Crée le pool de chauffeurs pour une commande
        Retourne la liste triée par priorité
        """
        # Trouver les chauffeurs proches
        nearby_drivers = self.order_service.find_nearby_drivers(
            float(order.pickup_latitude),
            float(order.pickup_longitude),
            vehicle_type_id=order.vehicle_type_id,
            limit=max_drivers
        )
        
        if not nearby_drivers:
            logger.warning(f"Aucun chauffeur trouvé pour la commande {order.id}")
            return []
        
        # Créer les entrées du pool
        pool_entries = []
        max_wait_time = self._get_config_value('MAX_DRIVER_WAITING_TIME', 30)
        timeout_at = timezone.now() + timedelta(seconds=max_wait_time)
        
        for index, driver_info in enumerate(nearby_drivers, 1):
            pool_entry = DriverPool.objects.create(
                order=order,
                driver_id=driver_info['driver_id'],
                priority_order=index,
                distance_km=driver_info['distance_km'],
                timeout_at=timeout_at,
                request_status='PENDING'
            )
            pool_entries.append(pool_entry)
        
        # Créer l'événement de tracking
        OrderTracking.objects.create(
            order=order,
            event_type='DRIVER_SEARCH_STARTED',
            metadata={
                'drivers_found': len(pool_entries),
                'max_distance': float(pool_entries[-1].distance_km) if pool_entries else 0
            }
        )
        
        logger.info(f"Pool créé pour commande {order.id}: {len(pool_entries)} chauffeurs")
        return pool_entries
    
    def get_next_available_driver(self, order: Order) -> Optional[DriverPool]:
        """
        Récupère le prochain chauffeur disponible dans le pool
        """
        now = timezone.now()
        
        # Marquer les timeouts
        DriverPool.objects.filter(
            order=order,
            request_status='PENDING',
            timeout_at__lt=now
        ).update(request_status='TIMEOUT')
        
        # Récupérer le prochain chauffeur en attente
        next_driver = DriverPool.objects.filter(
            order=order,
            request_status='PENDING'
        ).order_by('priority_order').first()
        
        if next_driver:
            # Créer l'événement de notification
            OrderTracking.objects.create(
                order=order,
                event_type='DRIVER_NOTIFIED',
                driver=next_driver.driver,
                metadata={
                    'priority': next_driver.priority_order,
                    'distance': float(next_driver.distance_km)
                }
            )
        
        return next_driver
    
    @transaction.atomic
    def handle_driver_response(self, pool_entry: DriverPool, accepted: bool, 
                              rejection_reason: str = '') -> bool:
        """
        Gère la réponse d'un chauffeur (acceptation ou refus)
        """
        if pool_entry.request_status != 'PENDING':
            logger.warning(f"Pool entry {pool_entry.id} n'est plus en attente")
            return False
        
        pool_entry.responded_at = timezone.now()
        
        if accepted:
            pool_entry.request_status = 'ACCEPTED'
            pool_entry.save()
            
            # Assigner le chauffeur à la commande
            order = pool_entry.order
            order.driver = pool_entry.driver
            order.status = 'ACCEPTED'
            order.accepted_at = timezone.now()
            order.save()
            
            # Annuler les autres requêtes du pool
            DriverPool.objects.filter(
                order=order,
                request_status='PENDING'
            ).update(request_status='CANCELLED')
            
            # Mettre à jour le statut du chauffeur
            driver_status = DriverStatus.objects.get(driver=pool_entry.driver)
            driver_status.status = 'BUSY'
            driver_status.save()
            
            # Créer l'événement
            OrderTracking.objects.create(
                order=order,
                event_type='DRIVER_ACCEPTED',
                driver=pool_entry.driver
            )
            
            logger.info(f"Chauffeur {pool_entry.driver.id} a accepté la commande {order.id}")
            return True
        else:
            pool_entry.request_status = 'REJECTED'
            pool_entry.rejection_reason = rejection_reason
            pool_entry.save()
            
            # Créer l'événement
            OrderTracking.objects.create(
                order=pool_entry.order,
                event_type='DRIVER_REJECTED',
                driver=pool_entry.driver,
                notes=rejection_reason
            )
            
            logger.info(f"Chauffeur {pool_entry.driver.id} a refusé la commande {pool_entry.order.id}")
            return False
    
    def check_pool_exhausted(self, order: Order) -> bool:
        """
        Vérifie si tous les chauffeurs du pool ont été contactés
        """
        pending_count = DriverPool.objects.filter(
            order=order,
            request_status='PENDING'
        ).count()
        
        return pending_count == 0
    
    def _get_config_value(self, search_key, default_value):
        """Helper pour récupérer une configuration"""
        try:
            config = GeneralConfig.objects.get(search_key=search_key, active=True)
            return config.get_numeric_value() or default_value
        except GeneralConfig.DoesNotExist:
            return default_value


class PaymentService:
    """Service pour gérer les paiements"""
    
    @transaction.atomic
    def process_payment(self, order: Order, payment_method_id: int = None) -> Dict:
        """
        Traite le paiement d'une commande
        """
        if order.payment_status == 'PAID':
            return {
                'success': False,
                'message': 'Cette commande a déjà été payée',
                'status': 'ALREADY_PAID'
            }
        
        # Utiliser la méthode de paiement de la commande ou celle fournie
        if payment_method_id:
            payment_method = PaymentMethod.objects.get(id=payment_method_id)
        else:
            payment_method = order.payment_method
        
        if not payment_method:
            return {
                'success': False,
                'message': 'Méthode de paiement non définie',
                'status': 'NO_PAYMENT_METHOD'
            }
        
        # Déterminer le montant à payer
        amount = order.final_price if order.final_price else order.total_price
        
        # Vérifier les limites de la méthode de paiement
        if payment_method.min_amount and amount < payment_method.min_amount:
            return {
                'success': False,
                'message': f'Montant minimum: {payment_method.min_amount} FCFA',
                'status': 'BELOW_MIN_AMOUNT'
            }
        
        if payment_method.max_amount and amount > payment_method.max_amount:
            return {
                'success': False,
                'message': f'Montant maximum: {payment_method.max_amount} FCFA',
                'status': 'ABOVE_MAX_AMOUNT'
            }
        
        # Traiter selon le type de paiement
        result = self._process_payment_by_type(order, payment_method, amount)
        
        if result['success']:
            order.payment_status = 'PAID'
            order.paid_at = timezone.now()
            order.save()
            
            # Créer l'événement
            OrderTracking.objects.create(
                order=order,
                event_type='PAYMENT_COMPLETED',
                metadata={
                    'amount': float(amount),
                    'method': payment_method.type
                }
            )
            
            # Mettre à jour les gains du chauffeur
            if order.driver:
                driver_status = DriverStatus.objects.get(driver=order.driver)
                driver_status.total_earnings_today = F('total_earnings_today') + amount
                driver_status.save()
        else:
            order.payment_status = 'FAILED'
            order.save()
            
            OrderTracking.objects.create(
                order=order,
                event_type='PAYMENT_FAILED',
                metadata={
                    'reason': result.get('message'),
                    'method': payment_method.type
                }
            )
        
        return result
    
    def _process_payment_by_type(self, order: Order, payment_method: PaymentMethod, 
                                amount: Decimal) -> Dict:
        """
        Traite le paiement selon le type de méthode
        """
        if payment_method.type == 'CASH':
            # Paiement en espèces - toujours succès car géré hors système
            return {
                'success': True,
                'message': 'Paiement en espèces enregistré',
                'status': 'CASH_REGISTERED',
                'amount': float(amount)
            }
        
        elif payment_method.type == 'WALLET':
            # Paiement par portefeuille
            return self._process_wallet_payment(order, amount)
        
        elif payment_method.type in ['OM', 'MOMO']:
            # Paiement mobile money
            return self._process_mobile_money_payment(order, payment_method, amount)
        
        else:
            return {
                'success': False,
                'message': 'Type de paiement non supporté',
                'status': 'UNSUPPORTED_TYPE'
            }
    
    def _process_wallet_payment(self, order: Order, amount: Decimal) -> Dict:
        """
        Traite le paiement par portefeuille
        """
        from api.models import Wallet
        
        try:
            wallet = Wallet.objects.get(user_customer=order.customer)
            
            if wallet.balance < amount:
                return {
                    'success': False,
                    'message': 'Solde insuffisant',
                    'status': 'INSUFFICIENT_BALANCE',
                    'balance': float(wallet.balance),
                    'required': float(amount)
                }
            
            # Débiter le portefeuille
            wallet.balance = F('balance') - amount
            wallet.save()
            
            return {
                'success': True,
                'message': 'Paiement par portefeuille réussi',
                'status': 'WALLET_SUCCESS',
                'amount': float(amount),
                'new_balance': float(wallet.balance)
            }
            
        except Wallet.DoesNotExist:
            return {
                'success': False,
                'message': 'Portefeuille non trouvé',
                'status': 'WALLET_NOT_FOUND'
            }
    
    def _process_mobile_money_payment(self, order: Order, payment_method: PaymentMethod, 
                                     amount: Decimal) -> Dict:
        """
        Traite le paiement par mobile money (OM/MOMO)
        TODO: Intégrer avec les APIs réelles Orange Money / MTN Mobile Money
        """
        # Pour l'instant, simulation
        logger.info(f"Simulation paiement {payment_method.type} de {amount} FCFA")
        
        # TODO: Implémenter l'intégration réelle avec les APIs
        # - Initialiser la transaction
        # - Attendre la confirmation de l'utilisateur
        # - Vérifier le statut de la transaction
        
        return {
            'success': True,
            'message': f'Paiement {payment_method.name} simulé',
            'status': 'SIMULATED_SUCCESS',
            'amount': float(amount),
            'transaction_id': f"SIM_{order.id}_{timezone.now().timestamp()}"
        }
    
    def refund_payment(self, order: Order, reason: str = '') -> Dict:
        """
        Rembourse un paiement
        """
        if order.payment_status != 'PAID':
            return {
                'success': False,
                'message': 'Cette commande n\'a pas été payée',
                'status': 'NOT_PAID'
            }
        
        # Traiter le remboursement selon le type
        if order.payment_method.type == 'WALLET':
            result = self._refund_wallet_payment(order)
        else:
            # Pour les autres méthodes, marquer comme remboursé
            result = {
                'success': True,
                'message': 'Remboursement enregistré',
                'status': 'REFUND_REGISTERED'
            }
        
        if result['success']:
            order.payment_status = 'REFUNDED'
            order.save()
            
            OrderTracking.objects.create(
                order=order,
                event_type='PAYMENT_REFUNDED',
                notes=reason,
                metadata=result
            )
        
        return result
    
    def _refund_wallet_payment(self, order: Order) -> Dict:
        """
        Rembourse un paiement par portefeuille
        """
        from api.models import Wallet
        
        amount = order.final_price if order.final_price else order.total_price
        
        try:
            wallet = Wallet.objects.get(user_customer=order.customer)
            wallet.balance = F('balance') + amount
            wallet.save()
            
            return {
                'success': True,
                'message': 'Remboursement effectué',
                'status': 'WALLET_REFUNDED',
                'amount': float(amount)
            }
            
        except Wallet.DoesNotExist:
            return {
                'success': False,
                'message': 'Portefeuille non trouvé',
                'status': 'WALLET_NOT_FOUND'
            }


class TrackingService:
    """Service pour gérer le tracking GPS des courses"""
    
    @transaction.atomic
    def record_position(self, order: Order, driver: UserDriver, 
                       latitude: float, longitude: float,
                       speed_kmh: float = None, heading: int = None,
                       accuracy: float = None) -> TripTracking:
        """
        Enregistre une position GPS pendant une course
        """
        tracking = TripTracking.objects.create(
            order=order,
            driver=driver,
            latitude=latitude,
            longitude=longitude,
            speed_kmh=speed_kmh,
            heading=heading,
            accuracy=accuracy,
            order_status=order.status
        )
        
        # Mettre à jour la position du chauffeur
        driver_status = DriverStatus.objects.get(driver=driver)
        driver_status.current_latitude = latitude
        driver_status.current_longitude = longitude
        driver_status.last_location_update = timezone.now()
        driver_status.save()
        
        return tracking
    
    def get_trip_path(self, order: Order) -> List[Dict]:
        """
        Récupère le chemin parcouru pendant une course
        """
        trackings = TripTracking.objects.filter(
            order=order
        ).order_by('recorded_at')
        
        path = []
        for tracking in trackings:
            path.append({
                'lat': float(tracking.latitude),
                'lng': float(tracking.longitude),
                'speed': float(tracking.speed_kmh) if tracking.speed_kmh else None,
                'heading': tracking.heading,
                'timestamp': tracking.recorded_at.isoformat(),
                'status': tracking.order_status
            })
        
        return path
    
    def calculate_actual_distance(self, order: Order) -> float:
        """
        Calcule la distance réelle parcourue basée sur le tracking GPS
        """
        trackings = TripTracking.objects.filter(
            order=order,
            order_status='IN_PROGRESS'
        ).order_by('recorded_at')
        
        if trackings.count() < 2:
            return 0
        
        total_distance = 0
        order_service = OrderService()
        
        for i in range(1, trackings.count()):
            prev = trackings[i-1]
            curr = trackings[i]
            
            distance = order_service.calculate_real_distance(
                float(prev.latitude), float(prev.longitude),
                float(curr.latitude), float(curr.longitude)
            )
            total_distance += distance
        
        return total_distance
    
    def detect_route_deviation(self, order: Order, threshold_km: float = 2.0) -> bool:
        """
        Détecte si le chauffeur dévie de l'itinéraire optimal
        """
        if order.status != 'IN_PROGRESS':
            return False
        
        # Récupérer la dernière position
        last_tracking = TripTracking.objects.filter(
            order=order
        ).order_by('-recorded_at').first()
        
        if not last_tracking:
            return False
        
        # Calculer la distance directe restante
        order_service = OrderService()
        direct_distance = order_service.calculate_real_distance(
            float(last_tracking.latitude),
            float(last_tracking.longitude),
            float(order.destination_latitude),
            float(order.destination_longitude)
        )
        
        # Calculer la distance parcourue
        actual_distance = self.calculate_actual_distance(order)
        
        # Si la distance parcourue + distance restante dépasse significativement
        # la distance estimée, il y a peut-être une déviation
        total_expected = float(order.estimated_distance_km)
        total_actual = actual_distance + direct_distance
        
        deviation = total_actual - total_expected
        
        if deviation > threshold_km:
            logger.warning(f"Déviation détectée pour commande {order.id}: {deviation:.2f} km")
            return True
        
        return False


class NotificationService:
    """Service pour gérer les notifications en temps réel"""
    
    def __init__(self, channel_layer=None):
        self.channel_layer = channel_layer
    
    async def notify_customer_order_accepted(self, customer_id: int, order_id: str, 
                                            driver_info: Dict):
        """Notifie le client que sa commande a été acceptée"""
        if not self.channel_layer:
            return
        
        await self.channel_layer.group_send(
            f'customer_{customer_id}',
            {
                'type': 'order_accepted',
                'order_id': str(order_id),
                'driver_info': driver_info,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def notify_customer_driver_arrived(self, customer_id: int, order_id: str):
        """Notifie le client que le chauffeur est arrivé"""
        if not self.channel_layer:
            return
        
        await self.channel_layer.group_send(
            f'customer_{customer_id}',
            {
                'type': 'driver_arrived',
                'order_id': str(order_id),
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def notify_customer_trip_started(self, customer_id: int, order_id: str):
        """Notifie le client que la course a commencé"""
        if not self.channel_layer:
            return
        
        await self.channel_layer.group_send(
            f'customer_{customer_id}',
            {
                'type': 'trip_started',
                'order_id': str(order_id),
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def notify_customer_trip_completed(self, customer_id: int, order_id: str, 
                                            final_price: float):
        """Notifie le client que la course est terminée"""
        if not self.channel_layer:
            return
        
        await self.channel_layer.group_send(
            f'customer_{customer_id}',
            {
                'type': 'trip_completed',
                'order_id': str(order_id),
                'final_price': final_price,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def notify_driver_location_to_customer(self, customer_id: int, order_id: str,
                                                latitude: float, longitude: float,
                                                speed: float = None):
        """Envoie la position du chauffeur au client"""
        if not self.channel_layer:
            return
        
        await self.channel_layer.group_send(
            f'customer_{customer_id}',
            {
                'type': 'driver_location_update',
                'order_id': str(order_id),
                'latitude': latitude,
                'longitude': longitude,
                'speed': speed,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def notify_driver_new_order(self, driver_id: int, order_data: Dict,
                                     timeout_seconds: int = 30):
        """Notifie un chauffeur d'une nouvelle commande"""
        if not self.channel_layer:
            return
        
        await self.channel_layer.group_send(
            f'driver_{driver_id}',
            {
                'type': 'new_order_request',
                'order_data': order_data,
                'timeout': timeout_seconds,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def notify_driver_order_cancelled(self, driver_id: int, order_id: str,
                                           reason: str = ''):
        """Notifie un chauffeur qu'une commande a été annulée"""
        if not self.channel_layer:
            return
        
        await self.channel_layer.group_send(
            f'driver_{driver_id}',
            {
                'type': 'order_cancelled',
                'order_id': str(order_id),
                'reason': reason,
                'timestamp': timezone.now().isoformat()
            }
        )
