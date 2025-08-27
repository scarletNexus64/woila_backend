#!/usr/bin/env python3
"""
Test rapide - à lancer quand le chauffeur est connecté
"""
import os
import sys
import django
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Configuration Django
sys.path.append('/Users/macbookpro/Desktop/Developments/Personnals/Woila/woila_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'woila_backend.settings')
django.setup()

def quick_test():
    print("🚀 TEST RAPIDE - Envoi notification au chauffeur 28")
    
    try:
        channel_layer = get_channel_layer()
        
        # Données simples pour le test
        order_data = {
            'id': 'test-urgent-999',
            'customer_name': 'TEST URGENT',
            'customer_phone': '+237999999999',
            'pickup_address': 'Test Address',
            'pickup_latitude': 3.8968711,
            'pickup_longitude': 11.5470538,
            'destination_address': 'Test Destination',
            'destination_latitude': 3.83599,
            'destination_longitude': 11.5505661,
            'estimated_distance_km': 2.0,
            'total_price': 1500.0,
            'vehicle_type': 'Standard',
            'customer_notes': 'TEST - Vérifiez AlertDialog',
            'timeout_seconds': 30,
            'created_at': '2025-01-28T12:00:00Z'
        }
        
        # Envoyer immédiatement
        async_to_sync(channel_layer.group_send)(
            'driver_28',
            {
                'type': 'order_request',
                'order_data': order_data
            }
        )
        
        print("✅ NOTIFICATION ENVOYÉE ! Vérifiez l'app chauffeur MAINTENANT !")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    quick_test()