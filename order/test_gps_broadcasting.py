"""
Tests unitaires pour la fonctionnalité de diffusion GPS automatique
==================================================================

Tests pour la diffusion automatique de la position GPS du chauffeur
lorsqu'il passe en ligne via l'API toggle_driver_status.
"""

import json
import asyncio
from unittest.mock import patch, AsyncMock
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from django.test import TransactionTestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from api.models import UserDriver, Token
from order.models import DriverStatus
from order.consumers import DriverConsumer


class GPSBroadcastingTestCase(TransactionTestCase):
    """
    Tests pour la diffusion GPS automatique
    """
    
    def setUp(self):
        """Configuration initiale des tests"""
        # Créer un utilisateur et un chauffeur de test
        self.user = User.objects.create_user(
            username='test_driver',
            email='driver@test.com',
            password='testpass123'
        )
        
        self.driver = UserDriver.objects.create(
            user=self.user,
            phone_number='+221701234567',
            license_number='DRV123456',
            is_active=True
        )
        
        # Créer un token d'authentification
        self.token = Token.objects.create(
            user=self.driver,
            user_type='driver'
        )
        
        # Client API pour les tests REST
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.key}')
        
        # Position GPS de test (Dakar, Sénégal)
        self.test_latitude = 14.6928
        self.test_longitude = -17.4467
    
    def test_toggle_driver_status_online(self):
        """
        Test: API toggle_driver_status passe le chauffeur ONLINE
        """
        print("\n🧪 Test 1: API toggle_driver_status -> ONLINE")
        
        # Appeler l'API
        response = self.client.post('/order/toggle-driver-status/')
        
        # Vérifications
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('status'), 'ONLINE')
        self.assertIn('en ligne', data.get('message', '').lower())
        
        # Vérifier en base de données
        driver_status = DriverStatus.objects.get(driver=self.driver)
        self.assertEqual(driver_status.status, 'ONLINE')
        
        print("✅ Chauffeur correctement passé en ligne")
    
    def test_toggle_driver_status_offline(self):
        """
        Test: API toggle_driver_status passe le chauffeur OFFLINE
        """
        print("\n🧪 Test 2: API toggle_driver_status -> OFFLINE")
        
        # D'abord passer en ligne
        DriverStatus.objects.create(driver=self.driver, status='ONLINE')
        
        # Appeler l'API pour repasser hors ligne
        response = self.client.post('/order/toggle-driver-status/')
        
        # Vérifications
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('status'), 'OFFLINE')
        self.assertIn('hors ligne', data.get('message', '').lower())
        
        # Vérifier en base de données
        driver_status = DriverStatus.objects.get(driver=self.driver)
        self.assertEqual(driver_status.status, 'OFFLINE')
        
        print("✅ Chauffeur correctement passé hors ligne")
    
    def test_update_driver_location_api(self):
        """
        Test: API update_driver_location met à jour la position GPS
        """
        print("\n🧪 Test 3: API update_driver_location")
        
        # Créer un status de chauffeur
        DriverStatus.objects.create(driver=self.driver, status='ONLINE')
        
        # Données de position
        location_data = {
            'latitude': self.test_latitude,
            'longitude': self.test_longitude
        }
        
        # Appeler l'API
        response = self.client.post('/order/update-driver-location/', location_data)
        
        # Vérifications
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data.get('success'))
        
        # Vérifier la position en base de données
        driver_status = DriverStatus.objects.get(driver=self.driver)
        self.assertEqual(float(driver_status.current_latitude), self.test_latitude)
        self.assertEqual(float(driver_status.current_longitude), self.test_longitude)
        self.assertIsNotNone(driver_status.last_location_update)
        
        print(f"✅ Position GPS mise à jour: ({self.test_latitude}, {self.test_longitude})")
    
    async def test_driver_websocket_connection(self):
        """
        Test: Connexion WebSocket du chauffeur avec diffusion GPS automatique
        """
        print("\n🧪 Test 4: WebSocket chauffeur - Connexion et diffusion GPS")
        
        # Créer un status et position de chauffeur
        await database_sync_to_async(DriverStatus.objects.create)(
            driver=self.driver,
            status='OFFLINE',
            current_latitude=self.test_latitude,
            current_longitude=self.test_longitude
        )
        
        # Établir la connexion WebSocket
        communicator = WebsocketCommunicator(DriverConsumer.as_asgi(), f"/ws/driver/{self.driver.id}/")
        connected, subprotocol = await communicator.connect()
        
        self.assertTrue(connected, "Connexion WebSocket échouée")
        
        try:
            # Vérifier le message de connexion
            response = await communicator.receive_json_from()
            self.assertEqual(response['type'], 'status_update')
            self.assertEqual(response['status'], 'ONLINE')
            
            print("✅ Connexion WebSocket établie, chauffeur mis en ligne")
            
            # Vérifier le démarrage de la diffusion GPS
            response = await communicator.receive_json_from()
            self.assertEqual(response['type'], 'location_broadcasting_started')
            self.assertIn('diffusion', response['message'].lower())
            
            print("✅ Diffusion GPS démarrée automatiquement")
            
            # Attendre et vérifier les messages de position (au moins 2 en 12 secondes)
            location_messages = []
            timeout_count = 0
            max_timeout = 24  # 12 secondes avec timeout de 0.5s
            
            while len(location_messages) < 2 and timeout_count < max_timeout:
                try:
                    response = await asyncio.wait_for(communicator.receive_json_from(), timeout=0.5)
                    
                    if response.get('type') == 'location_broadcast_confirmation':
                        location_messages.append(response)
                        lat = response.get('latitude')
                        lon = response.get('longitude')
                        print(f"📍 Position diffusée: ({lat}, {lon})")
                        
                except asyncio.TimeoutError:
                    timeout_count += 1
                    continue
            
            self.assertGreaterEqual(len(location_messages), 1, 
                                  "Aucune position GPS diffusée reçue")
            
            # Vérifier le contenu du message de position
            location_msg = location_messages[0]
            self.assertEqual(float(location_msg['latitude']), self.test_latitude)
            self.assertEqual(float(location_msg['longitude']), self.test_longitude)
            self.assertIsNotNone(location_msg.get('timestamp'))
            
            print(f"✅ {len(location_messages)} messages de position GPS reçus")
            
        finally:
            # Fermer la connexion
            await communicator.disconnect()
            
        print("✅ Test WebSocket terminé avec succès")
    
    @patch('order.views.async_to_sync')
    @patch('order.views.get_channel_layer')
    def test_gps_broadcasting_helper_functions(self, mock_get_channel_layer, mock_async_to_sync):
        """
        Test: Fonctions helper de diffusion GPS
        """
        print("\n🧪 Test 5: Fonctions helper de diffusion GPS")
        
        # Mock des objets WebSocket
        mock_channel_layer = AsyncMock()
        mock_get_channel_layer.return_value = mock_channel_layer
        mock_async_to_sync.return_value = AsyncMock()
        
        # Importer les fonctions après le mock
        from order.views import _start_driver_location_broadcasting, _stop_driver_location_broadcasting
        
        # Test démarrage diffusion
        _start_driver_location_broadcasting(self.driver.id)
        
        # Vérifier que les mocks ont été appelés
        mock_get_channel_layer.assert_called()
        mock_async_to_sync.assert_called()
        
        print("✅ Fonction de démarrage diffusion GPS testée")
        
        # Test arrêt diffusion
        _stop_driver_location_broadcasting(self.driver.id)
        
        print("✅ Fonction d'arrêt diffusion GPS testée")
    
    def test_driver_status_model(self):
        """
        Test: Modèle DriverStatus avec positions GPS
        """
        print("\n🧪 Test 6: Modèle DriverStatus")
        
        # Créer un status de chauffeur avec position
        driver_status = DriverStatus.objects.create(
            driver=self.driver,
            status='ONLINE',
            current_latitude=self.test_latitude,
            current_longitude=self.test_longitude
        )
        
        # Vérifications
        self.assertEqual(driver_status.driver, self.driver)
        self.assertEqual(driver_status.status, 'ONLINE')
        self.assertEqual(float(driver_status.current_latitude), self.test_latitude)
        self.assertEqual(float(driver_status.current_longitude), self.test_longitude)
        self.assertIsNotNone(driver_status.created_at)
        self.assertIsNotNone(driver_status.last_online)
        
        print("✅ Modèle DriverStatus fonctionne correctement")
    
    def run_async_test(self, coro):
        """Helper pour exécuter des tests asynchrones"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    
    def test_websocket_async(self):
        """Wrapper pour exécuter le test WebSocket asynchrone"""
        self.run_async_test(self.test_driver_websocket_connection())


class GPSBroadcastingIntegrationTest(TransactionTestCase):
    """
    Tests d'intégration pour la diffusion GPS complète
    """
    
    def setUp(self):
        """Configuration pour les tests d'intégration"""
        # Setup similaire au test unitaire
        self.user = User.objects.create_user(
            username='integration_driver',
            email='integration@test.com',
            password='testpass123'
        )
        
        self.driver = UserDriver.objects.create(
            user=self.user,
            phone_number='+221701234568',
            license_number='INT123456',
            is_active=True
        )
        
        self.token = Token.objects.create(
            user=self.driver,
            user_type='driver'
        )
        
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.key}')
    
    def test_complete_workflow(self):
        """
        Test d'intégration: Workflow complet de diffusion GPS
        """
        print("\n🧪 Test d'intégration: Workflow complet")
        
        # 1. Chauffeur hors ligne initialement
        self.assertFalse(
            DriverStatus.objects.filter(driver=self.driver, status='ONLINE').exists(),
            "Le chauffeur ne devrait pas être en ligne initialement"
        )
        
        # 2. Passer en ligne via API
        response = self.client.post('/order/toggle-driver-status/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get('status'), 'ONLINE')
        
        # 3. Mettre à jour la position GPS
        location_data = {'latitude': 14.6928, 'longitude': -17.4467}
        response = self.client.post('/order/update-driver-location/', location_data)
        self.assertEqual(response.status_code, 200)
        
        # 4. Vérifier l'état final
        driver_status = DriverStatus.objects.get(driver=self.driver)
        self.assertEqual(driver_status.status, 'ONLINE')
        self.assertEqual(float(driver_status.current_latitude), 14.6928)
        self.assertEqual(float(driver_status.current_longitude), -17.4467)
        
        # 5. Repasser hors ligne
        response = self.client.post('/order/toggle-driver-status/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get('status'), 'OFFLINE')
        
        # 6. Vérifier l'état final
        driver_status.refresh_from_db()
        self.assertEqual(driver_status.status, 'OFFLINE')
        
        print("✅ Workflow complet de diffusion GPS testé avec succès")


def run_tests():
    """
    Fonction pour exécuter tous les tests
    """
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    if not settings.configured:
        import os
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'woila_backend.settings')
        django.setup()
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["order.test_gps_broadcasting"])
    
    if failures:
        print(f"\n❌ {failures} test(s) échoué(s)")
        return False
    else:
        print("\n✅ Tous les tests sont passés !")
        return True


if __name__ == "__main__":
    """
    Exécution directe des tests
    """
    print("🚀 Tests de diffusion GPS automatique")
    print("=" * 50)
    
    success = run_tests()
    exit(0 if success else 1)