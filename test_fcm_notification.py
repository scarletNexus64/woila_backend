#!/usr/bin/env python3
"""
Test script pour déclencher une notification FCM de nouvelle commande
"""
import os
import sys
import django
from django.conf import settings

# Setup Django environment
sys.path.append('/Users/macbookpro/Desktop/Developments/Personnals/Woila/woila_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'woila_backend.settings')
django.setup()

from api.services.fcm_service import FCMService
from api.models import UserCustomer, UserDriver, FCMToken
import json

def test_new_order_fcm():
    """Test FCM notification pour une nouvelle commande"""
    
    print("🔍 Recherche des utilisateurs chauffeurs...")
    
    # Trouver un chauffeur avec token FCM via FCMToken
    fcm_tokens = FCMToken.objects.filter(user_type__model='userdriver')
    
    if not fcm_tokens.exists():
        print("❌ Aucun token FCM trouvé pour les chauffeurs")
        return
    
    # Récupérer les chauffeurs qui ont des tokens FCM
    driver_ids = fcm_tokens.values_list('user_id', flat=True)
    drivers = UserDriver.objects.filter(id__in=driver_ids)
    
    if not drivers.exists():
        print("❌ Aucun chauffeur avec token FCM trouvé")
        return
    
    driver = drivers.first()
    fcm_token = fcm_tokens.filter(user_id=driver.id).first()
    print(f"✅ Chauffeur trouvé: {driver.name} (ID: {driver.id})")
    print(f"📱 Token FCM: {fcm_token.token[:20]}...")
    
    # Données de test pour la commande
    order_data = {
        'order_id': '999',
        'customer_name': 'Test Customer',
        'estimated_distance_km': 5.2,
        'total_price': 2500,
        'pickup_address': 'Test Pickup Address',
        'destination_address': 'Test Destination Address',
        'customer_notes': 'Test order for FCM notification',
        'action_required': 'accept_or_decline',
        'timeout_seconds': '30'
    }
    
    print(f"\n📤 Envoi de notification FCM à {driver.name}...")
    
    try:
        success = FCMService.send_notification(
            user=driver,
            title="🚗 Nouvelle commande disponible!",
            body=f"{order_data['customer_name']} • {order_data['estimated_distance_km']:.1f} km • {order_data['total_price']:.0f} FCFA",
            data={
                'notification_type': 'new_order',
                'order_id': str(order_data['order_id']),
                'order_data': json.dumps(order_data),
                'action_required': 'accept_or_decline',
                'timeout_seconds': '30'
            },
            notification_type='new_order'
        )
        
        if success:
            print("✅ Notification FCM envoyée avec succès!")
            print(f"📱 Le chauffeur {driver.name} devrait recevoir l'AlertDialog")
            print("🔔 Vérifiez l'app chauffeur pour l'AlertDialog avec boutons Accept/Reject")
        else:
            print("❌ Échec de l'envoi de la notification FCM")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi FCM: {str(e)}")

if __name__ == "__main__":
    print("🚀 Test de notification FCM pour nouvelle commande")
    print("=" * 50)
    test_new_order_fcm()
    print("=" * 50)
    print("✅ Test terminé")