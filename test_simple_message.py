#!/usr/bin/env python3
"""
Test avec différents types de messages pour identifier le problème
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

def test_different_messages():
    print("🧪 TEST DES DIFFÉRENTS MESSAGES")
    
    try:
        channel_layer = get_channel_layer()
        
        # Test 1: test_group (on sait que ça marche)
        print("\n1. Test message test_group...")
        async_to_sync(channel_layer.group_send)(
            'driver_28',
            {
                'type': 'test_group',
                'message': 'Test group message'
            }
        )
        print("✅ test_group envoyé")
        
        # Test 2: order_request avec structure différente
        print("\n2. Test order_request simple...")
        async_to_sync(channel_layer.group_send)(
            'driver_28',
            {
                'type': 'order_request',
                'message': 'Test order request simple'
            }
        )
        print("✅ order_request simple envoyé")
        
        # Test 3: order_request avec order_data vide
        print("\n3. Test order_request avec order_data vide...")
        async_to_sync(channel_layer.group_send)(
            'driver_28',
            {
                'type': 'order_request',
                'order_data': {}
            }
        )
        print("✅ order_request vide envoyé")
        
        # Test 4: send_order_notification (autre nom)
        print("\n4. Test send_order_notification...")
        async_to_sync(channel_layer.group_send)(
            'driver_28',
            {
                'type': 'send_order_notification',
                'order_data': {'id': 'test-123', 'customer_name': 'Test'}
            }
        )
        print("✅ send_order_notification envoyé")
        
        print("\n🔍 Vérifiez les logs Flutter et Daphne maintenant...")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_different_messages()