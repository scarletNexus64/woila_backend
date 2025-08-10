#!/usr/bin/env python3
"""
Script de test pour vérifier les notifications FCM dans WOILA
Usage: python test_fcm_notifications.py
"""

import os
import sys
import django
from pathlib import Path

# Ajouter le répertoire du projet au path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'woila_backend.settings')
django.setup()

import logging
from api.models import UserDriver, Token, FCMToken
from api.services.fcm_service import FCMService

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_fcm_configuration():
    """Test de la configuration FCM de base"""
    print("🔧 Test de la configuration FCM...")
    
    try:
        # Test de l'obtention du token OAuth2
        oauth2_token = FCMService.get_firebase_oauth2_token()
        if oauth2_token:
            print("✅ Token OAuth2 Firebase obtenu avec succès")
            print(f"   Token préview: {oauth2_token[:30]}...")
            return True
        else:
            print("❌ Échec de l'obtention du token OAuth2")
            return False
    except Exception as e:
        print(f"❌ Erreur configuration FCM: {e}")
        return False

def test_user_sessions_and_tokens():
    """Test des sessions utilisateur et tokens FCM"""
    print("\n👤 Test des sessions utilisateur et tokens FCM...")
    
    try:
        # Récupérer tous les chauffeurs
        drivers = UserDriver.objects.filter(is_active=True)[:5]  # Limite à 5
        print(f"📊 {drivers.count()} chauffeur(s) actif(s) trouvé(s)")
        
        for driver in drivers:
            print(f"\n🔍 Test pour {driver.name} {driver.surname} (ID: {driver.id})")
            
            # Vérifier les sessions actives
            active_sessions = Token.objects.filter(
                user_type='driver',
                user_id=driver.id,
                is_active=True
            )
            
            print(f"   🔐 Sessions actives: {active_sessions.count()}")
            
            # Vérifier les tokens FCM
            fcm_tokens = FCMService.get_user_tokens(driver)
            print(f"   📱 Tokens FCM: {len(fcm_tokens)}")
            
            if fcm_tokens:
                for i, token in enumerate(fcm_tokens[:2], 1):  # Limite à 2 tokens
                    print(f"   📱 Token {i}: {token[:30]}...")
            
            if active_sessions.exists() and fcm_tokens:
                print(f"   ✅ {driver.name} peut recevoir des notifications")
            else:
                print(f"   ❌ {driver.name} ne peut pas recevoir de notifications")
                print(f"      - Session active: {'Oui' if active_sessions.exists() else 'Non'}")
                print(f"      - Token FCM: {'Oui' if fcm_tokens else 'Non'}")
        
        return True
    
    except Exception as e:
        print(f"❌ Erreur test utilisateurs: {e}")
        return False

def test_notification_send(driver_id=None):
    """Test d'envoi d'une notification"""
    print(f"\n📤 Test d'envoi de notification...")
    
    try:
        # Sélectionner un chauffeur pour le test
        if driver_id:
            try:
                driver = UserDriver.objects.get(id=driver_id, is_active=True)
            except UserDriver.DoesNotExist:
                print(f"❌ Chauffeur avec ID {driver_id} introuvable")
                return False
        else:
            # Trouver un chauffeur avec session active et token FCM
            drivers_with_sessions = []
            for driver in UserDriver.objects.filter(is_active=True)[:10]:
                has_session = Token.objects.filter(
                    user_type='driver',
                    user_id=driver.id,
                    is_active=True
                ).exists()
                
                has_tokens = bool(FCMService.get_user_tokens(driver))
                
                if has_session and has_tokens:
                    drivers_with_sessions.append(driver)
            
            if not drivers_with_sessions:
                print("❌ Aucun chauffeur avec session active et token FCM trouvé")
                return False
            
            driver = drivers_with_sessions[0]
        
        print(f"🎯 Test avec {driver.name} {driver.surname}")
        
        # Envoyer une notification de test
        success = FCMService.send_notification(
            user=driver,
            title="🧪 Test WOILA - Configuration",
            body=f"Bonjour {driver.name} ! Si vous recevez cette notification, la configuration FCM fonctionne parfaitement ! ✅",
            notification_type='system',
            data={
                'test_mode': True,
                'test_timestamp': str(django.utils.timezone.now().timestamp())
            }
        )
        
        if success:
            print("✅ Notification de test envoyée avec succès !")
            print("   Vérifiez votre application mobile pour confirmer la réception")
        else:
            print("❌ Échec de l'envoi de la notification de test")
        
        return success
    
    except Exception as e:
        print(f"❌ Erreur envoi notification: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚗 WOILA - Test des Notifications FCM")
    print("=" * 50)
    
    # Test 1: Configuration FCM
    config_ok = test_fcm_configuration()
    
    if not config_ok:
        print("\n❌ Configuration FCM échouée - Arrêt des tests")
        return
    
    # Test 2: Sessions et tokens utilisateur
    users_ok = test_user_sessions_and_tokens()
    
    # Test 3: Envoi de notification (optionnel)
    if users_ok:
        print("\n" + "=" * 50)
        response = input("Voulez-vous envoyer une notification de test ? (y/N): ")
        if response.lower() in ['y', 'yes', 'oui']:
            driver_id = input("ID du chauffeur (ou Entrée pour automatique): ")
            if driver_id.strip():
                try:
                    driver_id = int(driver_id)
                except ValueError:
                    driver_id = None
            else:
                driver_id = None
            
            test_notification_send(driver_id)
    
    print("\n✅ Tests terminés !")

if __name__ == "__main__":
    main()