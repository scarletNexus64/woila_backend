#!/usr/bin/env python
"""
Script de test manuel pour les WebSockets VTC
Usage: python test_websocket_manual.py
"""

import asyncio
import json
import websockets
import uuid
from datetime import datetime


async def test_driver_websocket():
    """Test de connexion WebSocket pour un driver"""
    driver_id = 1  # ID du driver de test
    uri = f"ws://localhost:8000/ws/driver/{driver_id}/"
    
    print(f"🚗 Connexion driver {driver_id}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Driver connecté!")
            
            # Recevoir le message de confirmation
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📨 Reçu: {data}")
            
            # Envoyer une mise à jour de position
            location_update = {
                "type": "location_update",
                "latitude": 4.0511,
                "longitude": 9.7679
            }
            await websocket.send(json.dumps(location_update))
            print("📍 Position mise à jour")
            
            # Attendre d'éventuels messages (demandes de course)
            print("⏳ En attente de commandes...")
            await asyncio.sleep(5)
            
    except Exception as e:
        print(f"❌ Erreur driver: {e}")


async def test_customer_websocket():
    """Test de connexion WebSocket pour un client"""
    customer_id = 1  # ID du client de test
    uri = f"ws://localhost:8000/ws/customer/{customer_id}/"
    
    print(f"👤 Connexion client {customer_id}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Client connecté!")
            
            # Créer une commande de test
            order_request = {
                "type": "create_order",
                "pickup_address": "Akwa, Douala",
                "pickup_latitude": 4.0511,
                "pickup_longitude": 9.7679,
                "destination_address": "Bonabéri, Douala", 
                "destination_latitude": 4.0300,
                "destination_longitude": 9.7100,
                "vehicle_type_id": 1,
                "city_id": 1,
                "distance_km": 8.5,
                "notes": "Test de commande via WebSocket"
            }
            
            await websocket.send(json.dumps(order_request))
            print("🚀 Commande envoyée")
            
            # Attendre la réponse
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📨 Reçu: {data}")
            
            # Attendre d'autres notifications
            await asyncio.sleep(10)
            
    except Exception as e:
        print(f"❌ Erreur client: {e}")


async def test_full_flow():
    """Test du flux complet: driver online + client commande"""
    print("🚀 Test du flux complet VTC WebSocket")
    print("=" * 50)
    
    # Lancer les deux connexions en parallèle
    await asyncio.gather(
        test_driver_websocket(),
        test_customer_websocket()
    )


def test_pricing_service():
    """Test rapide du service de pricing"""
    import os
    import sys
    import django
    
    # Configuration Django
    sys.path.append('/Users/boussastevejunior/Desktop/Dev/Personal/WOILA/Backend')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'woila_backend.settings')
    django.setup()
    
    from order.services import PricingService
    from api.models import VehicleType, City, Country
    
    print("\n💰 Test du service de pricing")
    print("-" * 30)
    
    try:
        # Créer les données de test si elles n'existent pas
        country, _ = Country.objects.get_or_create(
            name="Cameroun",
            defaults={'active': True}
        )
        
        vehicle_type, _ = VehicleType.objects.get_or_create(
            name="Sedan Standard",
            defaults={'additional_amount': 100.00}
        )
        
        city, _ = City.objects.get_or_create(
            name="Douala",
            country=country,
            defaults={
                'prix_jour': 50.00,
                'prix_nuit': 100.00,
                'active': True
            }
        )
        
        # Test du calcul de prix
        pricing_service = PricingService()
        
        result = pricing_service.calculate_order_price(
            vehicle_type_id=vehicle_type.id,
            city_id=city.id,
            distance_km=5.0,
            is_night=False
        )
        
        print(f"✅ Prix calculé:")
        print(f"   Base: {result['base_price']} XAF")
        print(f"   Distance: {result['distance_price']} XAF") 
        print(f"   Véhicule: {result['vehicle_additional_price']} XAF")
        print(f"   Ville: {result['city_price']} XAF")
        print(f"   TOTAL: {result['total_price']} XAF")
        
    except Exception as e:
        print(f"❌ Erreur pricing: {e}")


if __name__ == "__main__":
    print("🧪 Tests WebSocket VTC")
    print("=" * 30)
    
    # Test du service de pricing d'abord
    test_pricing_service()
    
    print("\n⚠️  INSTRUCTIONS:")
    print("1. Démarrer Redis: redis-server")
    print("2. Démarrer Django: python manage.py runserver")
    print("3. Relancer ce script")
    print("\nAppuyez sur Entrée pour tester les WebSockets...")
    input()
    
    # Test des WebSockets
    asyncio.run(test_full_flow())
    
    print("\n✅ Tests terminés!")