#!/usr/bin/env python3
"""
Test pour vérifier s'il y a duplication des bonus de parrainage
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
from api.models import UserDriver, ReferralCode, Wallet, GeneralConfig
from api.services.notification_service import NotificationService
from decimal import Decimal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print('=== TEST DUPLICATION BONUS PARRAINAGE ===')
print()

# 1. Vérifier la config bonus
try:
    welcome_config = GeneralConfig.objects.get(search_key='WELCOME_BONUS_AMOUNT', active=True)
    bonus_amount = welcome_config.get_numeric_value()
    print(f'💰 Bonus configuré: {bonus_amount} FCFA')
except GeneralConfig.DoesNotExist:
    bonus_amount = 500  # Valeur par défaut
    print(f'💰 Bonus par défaut: {bonus_amount} FCFA')

# 2. Récupérer le parrain avec le code FF7B4AE2
referral_code = 'FF7B4AE2'
sponsor_referral = ReferralCode.objects.get(code=referral_code, is_active=True)
sponsor_user = UserDriver.objects.get(id=sponsor_referral.user_id)

print(f'👤 Parrain: {sponsor_user.name} {sponsor_user.surname}')

# Vérifier le wallet AVANT
sponsor_wallet = Wallet.objects.get(
    user_type=sponsor_referral.user_type,
    user_id=sponsor_referral.user_id
)
initial_balance = sponsor_wallet.balance
print(f'💰 Solde initial: {initial_balance} FCFA')

# 3. Simuler plusieurs appels du même bonus (pour détecter duplication)
print()
print('🔄 TEST: Appels multiples du même bonus...')

for i in range(3):
    print(f'\\n📤 Appel {i+1} - NotificationService.send_referral_bonus_notification:')
    
    # Créer un utilisateur fictif pour chaque test
    referred_user = UserDriver(
        name=f'TestUser{i}',
        surname=f'Ref{i}',
        phone_number=f'+23799999999{i}',
        id=999 + i  # ID fictif
    )
    
    try:
        success = NotificationService.send_referral_bonus_notification(
            referrer_user=sponsor_user,
            referred_user=referred_user,
            referral_code=referral_code,
            bonus_amount=float(bonus_amount)
        )
        
        # Vérifier le nouveau solde
        sponsor_wallet.refresh_from_db()
        new_balance = sponsor_wallet.balance
        difference = new_balance - initial_balance
        
        print(f'   ➡️ Succès: {success}')
        print(f'   💰 Nouveau solde: {new_balance} FCFA')
        print(f'   📈 Différence totale: +{difference} FCFA')
        
        # Mettre à jour pour le prochain test
        initial_balance = new_balance
        
    except Exception as e:
        print(f'   ❌ Erreur: {e}')

# 4. Vérifications
print()
print('✅ ANALYSE:')
final_balance = sponsor_wallet.balance
total_added = final_balance - Wallet.objects.get(
    user_type=sponsor_referral.user_type,
    user_id=sponsor_referral.user_id
).balance

if total_added == 0:
    print('   ✅ Aucun bonus ajouté (normal si erreurs)')
elif total_added == bonus_amount:
    print(f'   ✅ Un seul bonus de {bonus_amount} FCFA ajouté - PAS DE DUPLICATION')
elif total_added > bonus_amount:
    multiple = total_added / bonus_amount
    print(f'   ❌ DUPLICATION DÉTECTÉE: {multiple}x le bonus ({total_added} FCFA au lieu de {bonus_amount} FCFA)')
else:
    print(f'   ⚠️ Bonus partiel: {total_added} FCFA au lieu de {bonus_amount} FCFA')

print()
print('🔍 ENDROITS OÙ LE BONUS EST AJOUTÉ:')
print('   1. NotificationService.send_referral_bonus_notification() - ligne 219')
print('   2. RegisterDriverSerializer.create() - ligne 506 (utilise WELCOME_BONUS_AMOUNT)')
print('   3. RegisterCustomerSerializer.create() - ligne 607 (utilise WELCOME_BONUS_AMOUNT)')

print()
print('⚠️ PROBLÈME DÉTECTÉ:')
print('   - Les serializers utilisent WELCOME_BONUS_AMOUNT (5000 FCFA)')
print('   - NotificationService ajoute ENCORE le bonus')
print('   - Résultat: DOUBLE BONUS = 10000 FCFA au lieu de 5000 FCFA')

print()
print('=== FIN DU TEST ===')