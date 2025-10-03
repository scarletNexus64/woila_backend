#!/usr/bin/env python3
"""
Test unitaire pour diagnostiquer le problème de recherche de chauffeurs
"""
import os
import sys
import django
import requests
import json
from decimal import Decimal

# Setup Django
sys.path.append('/Users/macbookpro/Desktop/Developments/Personnals/Woila/woila_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'woila_backend.settings')
django.setup()

from django.db import transaction
from api.models import UserDriver, UserCustomer, Vehicle, VehicleType, City, Country, Token
from order.models import DriverStatus
from order.services import OrderService

class DriverSearchTest:
    def __init__(self):
        self.base_url = "http://localhost:8000/api/v1"
        self.test_position = {
            "pickup_latitude": "3.8967862",
            "pickup_longitude": "11.5470146"
        }
        
    def print_separator(self, title):
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print('='*60)
        
    def check_database_state(self):
        """Vérifie l'état de la base de données"""
        self.print_separator("ÉTAT DE LA BASE DE DONNÉES")
        
        # Compter les chauffeurs
        total_drivers = UserDriver.objects.count()
        print(f"📊 Total chauffeurs: {total_drivers}")
        
        # Compter les statuts
        online_statuses = DriverStatus.objects.filter(status='ONLINE').count()
        offline_statuses = DriverStatus.objects.filter(status='OFFLINE').count()
        busy_statuses = DriverStatus.objects.filter(status='BUSY').count()
        
        print(f"🟢 Chauffeurs ONLINE: {online_statuses}")
        print(f"🔴 Chauffeurs OFFLINE: {offline_statuses}")
        print(f"🟡 Chauffeurs BUSY: {busy_statuses}")
        
        # Vérifier les positions GPS
        with_position = DriverStatus.objects.filter(
            status='ONLINE',
            current_latitude__isnull=False,
            current_longitude__isnull=False
        ).count()
        
        print(f"📍 Chauffeurs ONLINE avec position GPS: {with_position}")
        
        # Compter les véhicules
        total_vehicles = Vehicle.objects.count()
        active_vehicles = Vehicle.objects.filter(is_active=True).count()
        online_vehicles = Vehicle.objects.filter(is_active=True, is_online=True).count()
        
        print(f"🚗 Total véhicules: {total_vehicles}")
        print(f"✅ Véhicules actifs: {active_vehicles}")
        print(f"🌐 Véhicules en ligne: {online_vehicles}")
        
        return {
            'online_with_position': with_position,
            'online_vehicles': online_vehicles
        }
    
    def check_online_drivers_details(self):
        """Examine les détails des chauffeurs ONLINE"""
        self.print_separator("DÉTAILS CHAUFFEURS ONLINE")
        
        online_drivers = DriverStatus.objects.filter(status='ONLINE').select_related('driver')
        
        for driver_status in online_drivers:
            print(f"\n👤 Chauffeur: {driver_status.driver.name} {driver_status.driver.surname} (ID: {driver_status.driver.id})")
            print(f"   Status: {driver_status.status}")
            print(f"   Position: {driver_status.current_latitude}, {driver_status.current_longitude}")
            print(f"   Dernière MAJ: {driver_status.last_location_update}")
            
            # Vérifier les véhicules
            vehicles = Vehicle.objects.filter(driver=driver_status.driver)
            print(f"   Véhicules totaux: {vehicles.count()}")
            
            for vehicle in vehicles:
                print(f"   🚗 {vehicle.nom} - Actif: {vehicle.is_active}, En ligne: {vehicle.is_online}")
                print(f"      Type: {vehicle.vehicle_type.name if vehicle.vehicle_type else 'Aucun'}")
                print(f"      Plaque: {vehicle.plaque_immatriculation}")
    
    def create_test_data(self):
        """Crée des données de test si nécessaire"""
        self.print_separator("CRÉATION DONNÉES DE TEST")
        
        try:
            with transaction.atomic():
                # Vérifier s'il y a déjà un chauffeur test
                test_driver = UserDriver.objects.filter(email='test.driver@woila.com').first()
                
                if not test_driver:
                    print("🔧 Création d'un chauffeur test...")
                    
                    # Créer un chauffeur test
                    test_driver = UserDriver.objects.create(
                        email='test.driver@woila.com',
                        phone_number='+237600000001',
                        name='Test',
                        surname='Driver',
                        date_of_birth='1990-01-01',
                        is_verified=True
                    )
                    print(f"✅ Chauffeur créé: {test_driver.id}")
                
                # Créer/mettre à jour le statut
                driver_status, created = DriverStatus.objects.get_or_create(
                    driver=test_driver,
                    defaults={
                        'status': 'ONLINE',
                        'current_latitude': Decimal('3.8970000'),  # Proche de ta position
                        'current_longitude': Decimal('11.5470000')
                    }
                )
                
                if not created:
                    driver_status.status = 'ONLINE'
                    driver_status.current_latitude = Decimal('3.8970000')
                    driver_status.current_longitude = Decimal('11.5470000')
                    driver_status.save()
                
                print(f"✅ Statut chauffeur: ONLINE avec position GPS")
                
                # Vérifier le type de véhicule
                vehicle_type = VehicleType.objects.first()
                if not vehicle_type:
                    print("❌ Aucun type de véhicule trouvé")
                    return False
                
                # Créer/mettre à jour un véhicule test
                test_vehicle, created = Vehicle.objects.get_or_create(
                    driver=test_driver,
                    plaque_immatriculation='TEST-001',
                    defaults={
                        'vehicle_type': vehicle_type,
                        'nom': 'Véhicule Test',
                        'etat_vehicule': 8,
                        'is_active': True,
                        'is_online': True
                    }
                )
                
                if not created:
                    test_vehicle.is_active = True
                    test_vehicle.is_online = True
                    test_vehicle.save()
                
                print(f"✅ Véhicule: {test_vehicle.nom} - Actif et en ligne")
                
                return True
                
        except Exception as e:
            print(f"❌ Erreur création données test: {e}")
            return False
    
    def test_search_api(self):
        """Test l'API de recherche de chauffeurs"""
        self.print_separator("TEST API RECHERCHE CHAUFFEURS")
        
        url = f"{self.base_url}/order/customer/search-drivers/"
        
        payload = {
            "pickup_latitude": self.test_position["pickup_latitude"],
            "pickup_longitude": self.test_position["pickup_longitude"],
            "radius_km": 10
        }
        
        print(f"📤 URL: {url}")
        print(f"📝 Payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(url, json=payload)
            print(f"📥 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Réponse: {json.dumps(data, indent=2)}")
                
                if data.get('drivers_found', 0) > 0:
                    print("🎉 SUCCESS: Chauffeurs trouvés !")
                else:
                    print("⚠️  PROBLÈME: Aucun chauffeur trouvé")
                    
            else:
                print(f"❌ Erreur API: {response.text}")
                
        except Exception as e:
            print(f"❌ Erreur requête: {e}")
    
    def test_debug_apis(self):
        """Test les APIs de debug"""
        self.print_separator("TEST APIS DEBUG")
        
        # Test debug online drivers
        url = f"{self.base_url}/order/debug/online-drivers/"
        print(f"📤 Test: {url}")
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                print("✅ Debug online drivers:")
                print(json.dumps(data, indent=2))
            else:
                print(f"❌ Erreur debug online: {response.text}")
        except Exception as e:
            print(f"❌ Erreur debug online: {e}")
        
        # Test debug search
        url = f"{self.base_url}/order/debug/search-drivers/"
        payload = {
            "pickup_latitude": self.test_position["pickup_latitude"],
            "pickup_longitude": self.test_position["pickup_longitude"],
            "radius_km": 10
        }
        
        print(f"\n📤 Test: {url}")
        print(f"📝 Payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                print("✅ Debug search:")
                print(json.dumps(data, indent=2))
            else:
                print(f"❌ Erreur debug search: {response.text}")
        except Exception as e:
            print(f"❌ Erreur debug search: {e}")
    
    def run_full_test(self):
        """Lance tous les tests"""
        print("🚀 DÉMARRAGE DIAGNOSTIC RECHERCHE CHAUFFEURS")
        
        # 1. État base de données
        db_state = self.check_database_state()
        
        # 2. Détails chauffeurs online
        self.check_online_drivers_details()
        
        # 3. Créer données test si nécessaire
        if db_state['online_with_position'] == 0:
            print("\n⚠️  Aucun chauffeur online avec position, création de données test...")
            if self.create_test_data():
                print("✅ Données test créées, re-vérification...")
                self.check_database_state()
                self.check_online_drivers_details()
        
        # 4. Test APIs
        self.test_search_api()
        self.test_debug_apis()
        
        print(f"\n{'='*60}")
        print("🏁 DIAGNOSTIC TERMINÉ")
        print('='*60)

if __name__ == "__main__":
    tester = DriverSearchTest()
    tester.run_full_test()