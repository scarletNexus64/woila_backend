#!/usr/bin/env python3
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

def debug_groups():
    print("🔍 DEBUG GROUPES WEBSOCKET")
    
    try:
        channel_layer = get_channel_layer()
        print(f"Channel layer: {channel_layer}")
        
        # Test de différents groupes possibles
        groups_to_test = [
            'driver_28',
            'driver-28', 
            'drivers_28',
            'driver_pool_28',
            'chauffeur_28'
        ]
        
        for group_name in groups_to_test:
            print(f"\n📤 Testing group: '{group_name}'")
            try:
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        'type': 'test_group',
                        'message': f'Test pour groupe {group_name}'
                    }
                )
                print(f"✅ Envoyé à groupe: {group_name}")
            except Exception as e:
                print(f"❌ Erreur pour groupe {group_name}: {e}")
                
        # Test méthode que nous savons qui marche
        print(f"\n📤 Testing group 'driver_28' avec test_group...")
        async_to_sync(channel_layer.group_send)(
            'driver_28',
            {
                'type': 'test_group',
                'message': 'Test group message qui devrait marcher'
            }
        )
        
        print("\n🔍 Regardez les logs Flutter - quel groupe reçoit le message ?")
        
    except Exception as e:
        print(f"❌ Erreur globale: {e}")

if __name__ == "__main__":
    debug_groups()