#!/usr/bin/env python3
"""
Test de la recherche progressive des chauffeurs
"""
import os
import django
import sys

# Configuration Django
sys.path.append('/Users/macbookpro/Desktop/Developments/Personnals/Woila/woila_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'woila_backend.settings')

try:
    django.setup()
    from order.services import OrderService
    
    print("🚀 Test de la recherche progressive des chauffeurs")
    print("=" * 50)
    
    # Créer une instance du service
    order_service = OrderService()
    
    # Coordonnées de test (Douala, Cameroun)
    pickup_lat = 4.0030686
    pickup_lng = 9.8043635
    
    print(f"📍 Position de test: {pickup_lat}, {pickup_lng}")
    print()
    
    # Test 1: Recherche progressive normale
    print("🔍 Test 1: Recherche progressive")
    print("-" * 30)
    
    result = order_service.find_nearby_drivers_progressive(
        pickup_lat=pickup_lat,
        pickup_lng=pickup_lng,
        initial_radius_km=5,
        max_radius_km=30,
        step_km=5,
        min_drivers=1
    )
    
    print(f"✅ Chauffeurs trouvés: {len(result['drivers'])}")
    print(f"📏 Rayon utilisé: {result['radius_used_km']}km")
    print(f"🏁 Rayon max atteint: {result['max_radius_reached']}")
    print(f"🚗 Types de véhicules disponibles: {len(result['vehicle_types'])}")
    
    if result['drivers']:
        print("\n👥 Premiers chauffeurs trouvés:")
        for i, driver in enumerate(result['drivers'][:3]):
            print(f"  {i+1}. {driver['driver_name']} à {driver['distance_km']}km")
    else:
        print("⚠️ Aucun chauffeur trouvé dans la zone")
    
    print("\n" + "=" * 50)
    print("✅ Test terminé avec succès!")
    
except ImportError as e:
    print(f"❌ Erreur d'import Django: {e}")
    print("💡 Solution: Installer les dépendances avec 'pip install -r requirements.txt'")
except Exception as e:
    print(f"❌ Erreur: {e}")
    print(f"🔍 Type d'erreur: {type(e).__name__}")