#!/usr/bin/env python3
"""
Test complet du système de parrainage WOILA
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
from api.models import UserDriver, ReferralCode, Wallet, GeneralConfig, Notification, Token
from api.services.notification_service import NotificationService
from api.services.fcm_service import FCMService
from django.utils import timezone
from decimal import Decimal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print('=== TEST COMPLET SYSTÈME DE PARRAINAGE ===')
print()

# 1. Vérifier le code parrain et son propriétaire
referral_code = 'FF7B4AE2'
print(f'📋 Code parrain utilisé: {referral_code}')

# Récupérer le parrain
sponsor_referral = ReferralCode.objects.get(code=referral_code, is_active=True)
sponsor_user = UserDriver.objects.get(id=sponsor_referral.user_id)
print(f'👤 Parrain: {sponsor_user.name} {sponsor_user.surname} (ID: {sponsor_user.id})')

# Vérifier le wallet du parrain AVANT
sponsor_wallet = Wallet.objects.get(
    user_type=sponsor_referral.user_type,
    user_id=sponsor_referral.user_id
)
print(f'💰 Solde parrain AVANT: {sponsor_wallet.balance} FCFA')

# 2. Simuler l'inscription d'un nouveau chauffeur
print('\n📝 Inscription nouveau chauffeur avec code parrain...')
new_driver = UserDriver.objects.create(
    phone_number='+237699999999',
    password='test123',
    name='Nouveau',
    surname='Filleul',
    gender='M',
    age=25,
    birthday='1999-01-01',
    is_active=True
)
print(f'   ✅ Nouveau chauffeur créé: {new_driver.name} {new_driver.surname} (ID: {new_driver.id})')

# 3. Créer wallet et code parrain pour le nouveau
driver_content_type = ContentType.objects.get_for_model(UserDriver)
new_wallet, _ = Wallet.objects.get_or_create(
    user_type=driver_content_type,
    user_id=new_driver.id,
    defaults={'balance': 0}
)
new_referral = ReferralCode.objects.create(
    user_type=driver_content_type,
    user_id=new_driver.id
)
print(f'   📱 Code parrain du filleul: {new_referral.code}')

# 4. Créer une session pour le nouveau chauffeur (simule une connexion)
Token.objects.create(
    user_type='driver',
    user_id=new_driver.id,
    is_active=True
)
print(f'   🔐 Session créée pour le filleul')

# 5. Envoyer notification de bienvenue au nouveau
print('\n📤 TEST 1: Notification de bienvenue au filleul...')
welcome_success = NotificationService.send_welcome_notification(new_driver)
result_welcome = '✅ SUCCÈS' if welcome_success else '❌ ÉCHEC'
print(f'   ➡️ Résultat: {result_welcome}')

# 6. Traiter le bonus de parrainage et notification au parrain
print('\n📤 TEST 2: Bonus et notification au parrain...')
print(f'   💰 Bonus configuré: 500 FCFA')

# Envoyer notification au parrain avec bonus
referral_success = NotificationService.send_referral_bonus_notification(
    referrer_user=sponsor_user,
    referred_user=new_driver,
    referral_code=referral_code,
    bonus_amount=500.0
)
result_referral = '✅ SUCCÈS' if referral_success else '❌ ÉCHEC'
print(f'   ➡️ Résultat: {result_referral}')

# 7. Vérifications finales
print('\n✅ VÉRIFICATIONS FINALES:')

# Vérifier le nouveau solde du parrain
sponsor_wallet.refresh_from_db()
print(f'   💰 Nouveau solde parrain: {sponsor_wallet.balance} FCFA')

# Vérifier les notifications en base
parrain_notifications = Notification.objects.filter(
    user_type=driver_content_type,
    user_id=sponsor_user.id,
    notification_type='referral_used'
).order_by('-created_at')
print(f'   📬 Notifications parrainage du parrain: {parrain_notifications.count()}')

if parrain_notifications.exists():
    last_notif = parrain_notifications.first()
    print(f'      - Titre: {last_notif.title}')
    print(f'      - Créée: {last_notif.created_at}')

filleul_notifications = Notification.objects.filter(
    user_type=driver_content_type,
    user_id=new_driver.id,
    notification_type='welcome'
).order_by('-created_at')
print(f'   📬 Notifications bienvenue du filleul: {filleul_notifications.count()}')

if filleul_notifications.exists():
    last_notif = filleul_notifications.first()
    print(f'      - Titre: {last_notif.title}')
    print(f'      - Créée: {last_notif.created_at}')

print('\n=== FIN DU TEST ===')

# Nettoyer les données de test
print('\n🧹 Nettoyage...')
new_driver.delete()
print('   ✅ Utilisateur de test supprimé')