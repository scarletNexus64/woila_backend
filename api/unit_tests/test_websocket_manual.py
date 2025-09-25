#!/usr/bin/env python3
"""
Script de test manuel pour tester les notifications WebSocket
"""
import os
import sys
import django
import json
import asyncio
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Configuration Django
sys.path.append('/Users/macbookpro/Desktop/Developments/Personnals/Woila/woila_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'woila_backend.settings')
django.setup()

def test_websocket_notification():
    """Test d'envoi de notification WebSocket à un chauffeur"""
    
    print("🧪 === TEST NOTIFICATION WEBSOCKET ===")
    
    # ID du chauffeur à tester (remplacez par un ID valide)
    driver_id = input("Entrez l'ID du chauffeur à tester: ").strip()
    if not driver_id:
        driver_id = "28"  # Valeur par défaut
    
    print(f"📋 Test pour le chauffeur ID: {driver_id}")
    
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            print("❌ Channel layer non disponible")
            return
        
        print("✅ Channel layer OK")
        
        # Données de test pour la commande
        order_data = {
            'id': 'test-order-123',
            'customer_id': '1',
            'customer_name': 'Client Test',
            'customer_phone': '+237123456789',
            'pickup_address': 'Rue Test, Yaoundé',
            'pickup_latitude': 3.8968711,
            'pickup_longitude': 11.5470538,
            'destination_address': 'Destination Test, Yaoundé',
            'destination_latitude': 3.83599,
            'destination_longitude': 11.5505661,
            'estimated_distance_km': 5.2,
            'total_price': 2500.0,
            'vehicle_type': 'Standard',
            'customer_notes': 'Test de notification WebSocket',
            'timeout_seconds': 30,
            'created_at': '2025-01-28T12:00:00Z'
        }
        
        driver_group_name = f'driver_{driver_id}'
        
        print(f"📤 Envoi notification au groupe: {driver_group_name}")
        print(f"📦 Données de commande: {json.dumps(order_data, indent=2)}")
        
        # Envoyer la notification
        async_to_sync(channel_layer.group_send)(
            driver_group_name,
            {
                'type': 'order_request',
                'order_data': order_data
            }
        )
        
        print("✅ Notification envoyée avec succès!")
        print("🔍 Vérifiez l'app chauffeur pour voir si l'AlertDialog s'affiche")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi: {e}")

if __name__ == "__main__":
    test_websocket_notification()