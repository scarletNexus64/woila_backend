import json
import uuid
from decimal import Decimal
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from api.models import UserDriver, UserCustomer, VehicleType, City, VipZone, GeneralConfig
from .models import Order, DriverStatus, OrderTracking
from .consumers import DriverConsumer, CustomerConsumer
from .services import PricingService, OrderService


class PricingServiceTestCase(TestCase):
    """Tests pour le service de calcul des prix"""
    
    def setUp(self):
        # Créer les configurations
        GeneralConfig.objects.create(
            nom="Prix de base",
            search_key="STD_PRICELIST_ORDER",
            valeur="500",
            active=True
        )
        GeneralConfig.objects.create(
            nom="Prix par km",
            search_key="PRICE_PER_KM",
            valeur="250",
            active=True
        )
        
        # Créer les données de test
        self.vehicle_type = VehicleType.objects.create(
            name="Sedan",
            additional_amount=Decimal('100.00')
        )
        
        # Créer un pays d'abord
        from api.models import Country
        self.country = Country.objects.create(
            name="Cameroun",
            active=True
        )
        
        self.city = City.objects.create(
            country=self.country,
            name="Douala",
            prix_jour=Decimal('50.00'),
            prix_nuit=Decimal('100.00')
        )
        self.vip_zone = VipZone.objects.create(
            name="Zone Aéroport",
            prix_jour=Decimal('200.00'),
            prix_nuit=Decimal('300.00')
        )
        
        self.pricing_service = PricingService()
    
    def test_basic_price_calculation(self):
        """Test du calcul de prix de base"""
        result = self.pricing_service.calculate_order_price(
            vehicle_type_id=self.vehicle_type.id,
            city_id=self.city.id,
            distance_km=5.0,
            is_night=False
        )
        
        # Prix de base (500) + distance (5*250) + véhicule (100) + ville jour (50)
        expected_total = Decimal('500') + Decimal('1250') + Decimal('100') + Decimal('50')
        
        self.assertEqual(result['base_price'], Decimal('500'))
        self.assertEqual(result['distance_price'], Decimal('1250'))
        self.assertEqual(result['vehicle_additional_price'], Decimal('100'))
        self.assertEqual(result['city_price'], Decimal('50'))
        self.assertEqual(result['total_price'], expected_total)
        self.assertFalse(result['is_night_fare'])
    
    def test_night_fare_calculation(self):
        """Test du calcul de prix de nuit"""
        result = self.pricing_service.calculate_order_price(
            vehicle_type_id=self.vehicle_type.id,
            city_id=self.city.id,
            distance_km=3.0,
            is_night=True
        )
        
        # Prix de nuit pour la ville
        self.assertEqual(result['city_price'], Decimal('100'))
        self.assertTrue(result['is_night_fare'])
    
    def test_vip_zone_calculation(self):
        """Test du calcul avec zone VIP"""
        result = self.pricing_service.calculate_order_price(
            vehicle_type_id=self.vehicle_type.id,
            city_id=self.city.id,
            distance_km=2.0,
            vip_zone_id=self.vip_zone.id,
            is_night=False
        )
        
        # Prix de base zone VIP jour
        self.assertEqual(result['vip_zone_price'], Decimal('200'))
    
    def test_is_night_time(self):
        """Test de la détection heure de nuit"""
        from datetime import time
        
        # Test heure de jour
        self.assertFalse(self.pricing_service.is_night_time(time(14, 0)))
        
        # Test heure de nuit
        self.assertTrue(self.pricing_service.is_night_time(time(23, 0)))
        self.assertTrue(self.pricing_service.is_night_time(time(2, 0)))


class OrderServiceTestCase(TestCase):
    """Tests pour le service de gestion des commandes"""
    
    def setUp(self):
        self.driver = UserDriver.objects.create(
            phone_number="237600000001",
            password="test123",
            name="John",
            surname="Doe",
            gender="M",
            age=30,
            birthday="1993-01-01"
        )
        
        self.customer = UserCustomer.objects.create(
            phone_number="237600000002",
            password="test123",
            name="Jane",
            surname="Smith"
        )
        
        self.driver_status = DriverStatus.objects.create(
            driver=self.driver,
            status='ONLINE',
            current_latitude=Decimal('4.0511'),
            current_longitude=Decimal('9.7679')
        )
        
        self.order_service = OrderService()
    
    def test_find_nearby_drivers(self):
        """Test de recherche de chauffeurs à proximité"""
        drivers = self.order_service.find_nearby_drivers(
            pickup_lat=4.0500,  # Proche de la position du driver
            pickup_lng=9.7700,
            radius_km=5
        )
        
        self.assertEqual(len(drivers), 1)
        self.assertEqual(drivers[0].driver, self.driver)
    
    def test_calculate_distance(self):
        """Test du calcul de distance"""
        distance = self.order_service.calculate_distance(
            lat1=4.0511, lng1=9.7679,  # Douala
            lat2=3.8480, lng2=11.5021  # Yaoundé
        )
        
        # Distance approximative Douala-Yaoundé ≈ 194km (calcul correct)
        self.assertGreater(distance, 180)
        self.assertLess(distance, 220)
    
    def test_status_transitions(self):
        """Test des transitions de statut"""
        # Transitions valides
        self.assertTrue(self.order_service.can_transition_status('PENDING', 'ACCEPTED'))
        self.assertTrue(self.order_service.can_transition_status('ACCEPTED', 'IN_PROGRESS'))
        self.assertTrue(self.order_service.can_transition_status('IN_PROGRESS', 'COMPLETED'))
        
        # Transitions invalides
        self.assertFalse(self.order_service.can_transition_status('PENDING', 'COMPLETED'))
        self.assertFalse(self.order_service.can_transition_status('COMPLETED', 'IN_PROGRESS'))


class ModelTestCase(TestCase):
    """Tests pour les modèles"""
    
    def setUp(self):
        self.driver = UserDriver.objects.create(
            phone_number="237600000001",
            password="test123",
            name="John",
            surname="Doe",
            gender="M",
            age=30,
            birthday="1993-01-01"
        )
        
        self.customer = UserCustomer.objects.create(
            phone_number="237600000002",
            password="test123",
            name="Jane",
            surname="Smith"
        )
        
        self.vehicle_type = VehicleType.objects.create(
            name="Sedan",
            additional_amount=Decimal('100.00')
        )
        
        # Créer un pays d'abord
        from api.models import Country
        self.country = Country.objects.create(
            name="Cameroun",
            active=True
        )
        
        self.city = City.objects.create(
            country=self.country,
            name="Douala",
            prix_jour=Decimal('50.00'),
            prix_nuit=Decimal('100.00')
        )
    
    def test_order_creation(self):
        """Test de création d'une commande"""
        order = Order.objects.create(
            customer=self.customer,
            pickup_address="Akwa, Douala",
            pickup_latitude=Decimal('4.0511'),
            pickup_longitude=Decimal('9.7679'),
            destination_address="Bonabéri, Douala",
            destination_latitude=Decimal('4.0300'),
            destination_longitude=Decimal('9.7100'),
            vehicle_type=self.vehicle_type,
            city=self.city,
            estimated_distance_km=Decimal('8.50'),
            base_price=Decimal('500.00'),
            distance_price=Decimal('2125.00'),
            total_price=Decimal('2625.00')
        )
        
        self.assertEqual(order.status, 'PENDING')
        self.assertEqual(order.customer, self.customer)
        self.assertIsNone(order.driver)
        self.assertEqual(str(order), f"Commande {order.id} - {self.customer} → PENDING")
    
    def test_driver_status_creation(self):
        """Test de création du statut chauffeur"""
        status = DriverStatus.objects.create(
            driver=self.driver,
            status='ONLINE',
            current_latitude=Decimal('4.0511'),
            current_longitude=Decimal('9.7679')
        )
        
        self.assertEqual(status.status, 'ONLINE')
        self.assertEqual(status.driver, self.driver)
        self.assertEqual(str(status), f"{self.driver} - En ligne")
    
    def test_order_tracking_creation(self):
        """Test de création d'un événement de suivi"""
        order = Order.objects.create(
            customer=self.customer,
            pickup_address="Test",
            pickup_latitude=Decimal('4.0511'),
            pickup_longitude=Decimal('9.7679'),
            destination_address="Test",
            destination_latitude=Decimal('4.0300'),
            destination_longitude=Decimal('9.7100'),
            vehicle_type=self.vehicle_type,
            city=self.city,
            estimated_distance_km=Decimal('8.50'),
            base_price=Decimal('500.00'),
            distance_price=Decimal('2125.00'),
            total_price=Decimal('2625.00')
        )
        
        tracking = OrderTracking.objects.create(
            order=order,
            event_type='ORDER_CREATED',
            latitude=Decimal('4.0511'),
            longitude=Decimal('9.7679'),
            metadata={'test': 'data'}
        )
        
        self.assertEqual(tracking.event_type, 'ORDER_CREATED')
        self.assertEqual(tracking.order, order)
        self.assertEqual(tracking.metadata, {'test': 'data'})


class WebSocketTestCase(TransactionTestCase):
    """Tests pour les WebSockets"""
    
    def setUp(self):
        self.driver = UserDriver.objects.create(
            phone_number="237600000001",
            password="test123",
            name="John",
            surname="Doe",
            gender="M",
            age=30,
            birthday="1993-01-01"
        )
        
        self.customer = UserCustomer.objects.create(
            phone_number="237600000002",
            password="test123",
            name="Jane",
            surname="Smith"
        )
    
    async def test_driver_connection(self):
        """Test de connexion d'un driver"""
        communicator = WebsocketCommunicator(
            DriverConsumer.as_asgi(),
            f"/ws/driver/{self.driver.id}/"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Vérifier que le driver est marqué comme ONLINE
        driver_status = await database_sync_to_async(
            DriverStatus.objects.get
        )(driver_id=self.driver.id)
        self.assertEqual(driver_status.status, 'ONLINE')
        
        # Recevoir le message de confirmation
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'status_update')
        self.assertEqual(response['status'], 'ONLINE')
        
        await communicator.disconnect()
    
    async def test_driver_location_update(self):
        """Test de mise à jour de position du driver"""
        communicator = WebsocketCommunicator(
            DriverConsumer.as_asgi(),
            f"/ws/driver/{self.driver.id}/"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Envoyer une mise à jour de position
        await communicator.send_json_to({
            'type': 'location_update',
            'latitude': 4.0511,
            'longitude': 9.7679
        })
        
        # Vérifier que la position a été mise à jour
        driver_status = await database_sync_to_async(
            DriverStatus.objects.get
        )(driver_id=self.driver.id)
        self.assertEqual(float(driver_status.current_latitude), 4.0511)
        self.assertEqual(float(driver_status.current_longitude), 9.7679)
        
        await communicator.disconnect()
    
    async def test_customer_connection(self):
        """Test de connexion d'un client"""
        communicator = WebsocketCommunicator(
            CustomerConsumer.as_asgi(),
            f"/ws/customer/{self.customer.id}/"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        await communicator.disconnect()


def run_websocket_tests():
    """Fonction pour exécuter les tests WebSocket de manière asynchrone"""
    import asyncio
    
    async def run_tests():
        test_case = WebSocketTestCase()
        test_case.setUp()
        
        print("🧪 Test de connexion driver...")
        await test_case.test_driver_connection()
        print("✅ Driver connection test passed")
        
        print("🧪 Test de mise à jour de position...")
        await test_case.test_driver_location_update()
        print("✅ Location update test passed")
        
        print("🧪 Test de connexion client...")
        await test_case.test_customer_connection()
        print("✅ Customer connection test passed")
        
        print("🎉 Tous les tests WebSocket sont passés!")
    
    asyncio.run(run_tests())
