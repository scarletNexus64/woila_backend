#!/usr/bin/env python3
"""
Test du système de parrainage APRÈS correction de la duplication
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
from api.models import UserDriver, ReferralCode, Wallet, GeneralConfig, Notification
from api.serializers import RegisterDriverSerializer
from decimal import Decimal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

print('=== TEST PARRAINAGE APRÈS CORRECTION ===')
print()

# 1. État initial du parrain
referral_code = 'FF7B4AE2'
sponsor_referral = ReferralCode.objects.get(code=referral_code, is_active=True)
sponsor_user = UserDriver.objects.get(id=sponsor_referral.user_id)
sponsor_wallet = Wallet.objects.get(
    user_type=sponsor_referral.user_type,
    user_id=sponsor_referral.user_id
)

print(f'👤 Parrain: {sponsor_user.name} {sponsor_user.surname}')
print(f'💰 Solde initial: {sponsor_wallet.balance} FCFA')

# 2. Bonus configuré
try:
    welcome_config = GeneralConfig.objects.get(search_key='WELCOME_BONUS_AMOUNT', active=True)
    bonus_amount = welcome_config.get_numeric_value()
    print(f'⚙️ Bonus configuré: {bonus_amount} FCFA')
except:
    bonus_amount = 5000
    print(f'⚙️ Bonus par défaut: {bonus_amount} FCFA')

# 3. Simuler une inscription avec code parrain
print()
print('📝 Simulation inscription avec code parrain...')

# Données d'inscription
registration_data = {
    'phone_number': '+237688777666',
    'password': 'test123',
    'confirm_password': 'test123',
    'name': 'TestCorrection',
    'surname': 'User',
    'gender': 'M',
    'age': 25,
    'birthday': '1999-01-01',
    'referral_code': referral_code
}

# Utiliser le serializer comme le ferait l'API
serializer = RegisterDriverSerializer(data=registration_data)

if serializer.is_valid():
    print('✅ Données valides')
    
    # Créer l'utilisateur (cela doit ajouter le bonus UNE SEULE FOIS)
    try:
        new_driver = serializer.save()
        print(f'✅ Nouveau chauffeur créé: {new_driver.name} {new_driver.surname} (ID: {new_driver.id})')
        
        # Vérifier le nouveau solde du parrain
        sponsor_wallet.refresh_from_db()
        new_balance = sponsor_wallet.balance
        difference = new_balance - Decimal('1000')  # 1000 était le solde initial
        
        print()
        print('💰 RÉSULTAT FINANCIER:')
        print(f'   Solde avant: 1000 FCFA')
        print(f'   Solde après: {new_balance} FCFA')
        print(f'   Différence: +{difference} FCFA')
        
        if difference == Decimal(str(bonus_amount)):
            print(f'   ✅ PARFAIT: Un seul bonus de {bonus_amount} FCFA ajouté')
        elif difference == Decimal(str(bonus_amount * 2)):
            print(f'   ❌ PROBLÈME: Double bonus détecté ({difference} FCFA)')
        elif difference == 0:
            print(f'   ❌ ERREUR: Aucun bonus ajouté')
        else:
            print(f'   ⚠️ ÉTRANGE: Montant inattendu (+{difference} FCFA)')
        
        # Vérifier les notifications
        print()
        print('📬 NOTIFICATIONS:')
        driver_content_type = ContentType.objects.get_for_model(UserDriver)
        
        # Notifications du parrain (parrainage)
        parrain_notifications = Notification.objects.filter(
            user_type=driver_content_type,
            user_id=sponsor_user.id,
            notification_type='referral_used'
        ).count()
        print(f'   Notifications parrain: {parrain_notifications}')
        
        # Notifications du nouveau (bienvenue - doit être 0 car désactivé)
        filleul_notifications = Notification.objects.filter(
            user_type=driver_content_type,
            user_id=new_driver.id,
            notification_type='welcome'
        ).count()
        print(f'   Notifications filleul: {filleul_notifications} (doit être 0)')
        
        # Nettoyage
        print()
        print('🧹 Nettoyage...')
        new_driver.delete()
        print('   ✅ Utilisateur de test supprimé')
        
    except Exception as e:
        print(f'❌ Erreur lors de l\'inscription: {e}')
        import traceback
        traceback.print_exc()

else:
    print('❌ Données invalides:', serializer.errors)

print()
print('=== FIN DU TEST ===')
print()
print('📋 RÉSUMÉ DES CORRECTIONS APPLIQUÉES:')
print('   1. NotificationService.send_referral_bonus_notification() ne modifie plus le wallet')
print('   2. Seul le RegisterSerializer ajoute le bonus (UNE FOIS)')
print('   3. Correction du sponsor_referral.user vers sponsor_user_model.objects.get()')
print('   4. Notification de bienvenue différée au premier login')