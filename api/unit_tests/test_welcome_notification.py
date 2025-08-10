#!/usr/bin/env python3
"""
Test de la notification de bienvenue lors du premier login
"""
import os
import sys
import django
from pathlib import Path

# Setup Django
project_root = Path(__file__).parent
sys.path.append(str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'woila_backend.settings')
django.setup()

import logging
from django.contrib.contenttypes.models import ContentType
from api.models import UserDriver, ReferralCode, Wallet, GeneralConfig, Notification, Token, FCMToken
from api.viewsets.login import LoginView
from api.services.notification_service import NotificationService
from django.http import HttpRequest
from django.utils import timezone
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print('=== TEST NOTIFICATION DE BIENVENUE AU PREMIER LOGIN ===')
print()

# 1. Créer un nouvel utilisateur (simule une inscription)
print('📝 1. Inscription d\'un nouveau chauffeur...')
new_driver = UserDriver.objects.create(
    phone_number='+237688888888',
    password='test123',
    name='TestWelcome',
    surname='User',
    gender='M',
    age=25,
    birthday='1999-01-01',
    is_active=True
)
print(f'   ✅ Nouveau chauffeur créé: {new_driver.name} {new_driver.surname} (ID: {new_driver.id})')

# Créer wallet et code parrain
driver_content_type = ContentType.objects.get_for_model(UserDriver)
Wallet.objects.get_or_create(
    user_type=driver_content_type,
    user_id=new_driver.id,
    defaults={'balance': 0}
)
referral = ReferralCode.objects.create(
    user_type=driver_content_type,
    user_id=new_driver.id
)
print(f'   📱 Code parrain: {referral.code}')

# 2. Premier login (simule la connexion depuis l'app)
print('\n🔑 2. Premier login du chauffeur...')
print('   ⏳ Création du token de session...')

# Simuler le login - créer le token comme le fait LoginView
token = Token.objects.create(
    user_type='driver',
    user_id=new_driver.id
)
print(f'   ✅ Token créé: {token.token}')

# Vérifier si c'est le premier login
previous_tokens_count = Token.objects.filter(
    user_type='driver',
    user_id=new_driver.id
).exclude(id=token.id).count()

print(f'   🔍 Tokens précédents: {previous_tokens_count}')

if previous_tokens_count == 0:
    # Vérifier s'il n'a pas déjà reçu de notification de bienvenue
    welcome_notifications = Notification.objects.filter(
        user_type=driver_content_type,
        user_id=new_driver.id,
        notification_type='welcome'
    ).exists()
    
    print(f'   📬 Notifications bienvenue existantes: {welcome_notifications}')
    
    if not welcome_notifications:
        print('   📤 Envoi notification de bienvenue différée (2s)...')
        
        # Simuler l'envoi du token FCM après le login
        print('   📱 Simulation envoi token FCM...')
        fcm_token = FCMToken.objects.create(
            user=new_driver,
            token='fake_token_for_test_' + str(new_driver.id),
            platform='android',
            device_id='test_device_' + str(new_driver.id)
        )
        print(f'   ✅ Token FCM enregistré: {fcm_token.token[:30]}...')
        
        # Attendre 2 secondes puis envoyer la notification
        time.sleep(2)
        
        try:
            success = NotificationService.send_welcome_notification(new_driver)
            print(f'   ➡️ Résultat: {"✅ SUCCÈS" if success else "❌ ÉCHEC"}')
        except Exception as e:
            print(f'   ❌ Erreur: {e}')

# 3. Vérifications finales
print('\n✅ 3. VÉRIFICATIONS FINALES:')

# Vérifier les notifications en base
welcome_notifications = Notification.objects.filter(
    user_type=driver_content_type,
    user_id=new_driver.id,
    notification_type='welcome'
).order_by('-created_at')

print(f'   📬 Notifications bienvenue: {welcome_notifications.count()}')
if welcome_notifications.exists():
    last_notif = welcome_notifications.first()
    print(f'      - Titre: {last_notif.title}')
    print(f'      - Créée: {last_notif.created_at}')
    print(f'      - Lue: {last_notif.is_read}')

# Vérifier les tokens FCM
fcm_tokens = FCMToken.objects.filter(user=new_driver, is_active=True)
print(f'   📱 Tokens FCM actifs: {fcm_tokens.count()}')

print('\n🧹 Nettoyage...')
new_driver.delete()  # Supprime aussi les objets liés
print('   ✅ Utilisateur de test supprimé')

print('\n=== FLUX RECOMMANDÉ ===')
print('1. 📝 Inscription → PAS de notification (pas de token FCM)')
print('2. 🔑 Login → Création session + Délai 2s')
print('3. 📱 App envoie token FCM')
print('4. 📤 Backend envoie notification bienvenue')
print('5. ✅ Utilisateur reçoit notification avec token FCM')

print('\n=== FIN DU TEST ===')