import logging
from decimal import Decimal
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from typing import Dict, Optional, Any
import time

from ..models import Wallet, WalletTransaction, UserDriver, UserCustomer
from .freemopay import FreemoPayDirect

logger = logging.getLogger(__name__)


class WalletService:
    """Service pour gérer les opérations de wallet avec FreeMoPay"""
    
    @staticmethod
    def get_content_type_for_user(user_type: str):
        """Obtenir le ContentType correct pour un type d'utilisateur"""
        if user_type == 'driver':
            return ContentType.objects.get(app_label='api', model='userdriver')
        elif user_type == 'customer':
            return ContentType.objects.get(app_label='api', model='usercustomer')
        else:
            raise ValueError(f"Type d'utilisateur invalide: {user_type}")
    
    @staticmethod
    def get_or_create_wallet(user, user_type: str) -> Wallet:
        """Obtenir ou créer un wallet pour un utilisateur"""
        content_type = WalletService.get_content_type_for_user(user_type)
        
        wallet, created = Wallet.objects.get_or_create(
            user_type=content_type,
            user_id=user.id,
            defaults={'balance': Decimal('0.00')}
        )
        
        if created:
            logger.info(f"Nouveau wallet créé pour {user} ({user_type})")
        
        return wallet
    
    @staticmethod
    def get_wallet_balance(user, user_type: str) -> Decimal:
        """Obtenir le solde du wallet d'un utilisateur"""
        try:
            wallet = WalletService.get_or_create_wallet(user, user_type)
            return wallet.balance
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du solde pour {user}: {str(e)}")
            return Decimal('0.00')
    
    @staticmethod
    def initiate_deposit(
        user, 
        user_type: str, 
        amount: Decimal, 
        phone_number: str,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Initier un dépôt d'argent dans le wallet
        """
        try:
            # Obtenir ou créer le wallet
            wallet = WalletService.get_or_create_wallet(user, user_type)
            
            content_type = WalletService.get_content_type_for_user(user_type)
            
            # Créer la transaction en attente
            wallet_transaction = WalletTransaction.objects.create(
                user_type=content_type,
                user_id=user.id,
                transaction_type='deposit',
                amount=amount,
                status='pending',
                payment_method='mobile_money',
                phone_number=phone_number,
                balance_before=wallet.balance,
                balance_after=wallet.balance,  # Sera mis à jour après confirmation
                description=description or f"Dépôt de {amount} FCFA",
                metadata={
                    'user_type': user_type,
                    'phone_number': phone_number,
                    'initiated_at': timezone.now().isoformat()
                }
            )
            
            # Initier le paiement avec FreeMoPay
            logger.info(f"[WalletService] Initialisation du paiement FreeMoPay pour {amount} FCFA...")
            freemopay_result = FreemoPayDirect.init_payment(
                payer=phone_number,
                amount=float(amount),
                external_id=wallet_transaction.reference,
                description=wallet_transaction.description,
                callback=""  # Pas de callback, on utilise le polling
            )
            
            logger.debug(f"[WalletService] Réponse init_payment: {freemopay_result}")
            
            # Vérifier si l'initialisation a réussi
            init_status = freemopay_result.get('status')
            if init_status == 'FAILED':
                error_msg = freemopay_result.get('message', 'Échec de l\'initialisation du paiement')
                logger.error(f"[WalletService] Échec de l'initialisation: {error_msg}")
                wallet_transaction.mark_as_failed(error_msg)
                
                return {
                    'success': False,
                    'transaction_reference': wallet_transaction.reference,
                    'message': error_msg,
                    'error': freemopay_result
                }
            
            # Récupérer la référence
            reference = freemopay_result.get('reference')
            if not reference:
                error_msg = 'Pas de référence de paiement retournée par FreeMoPay'
                logger.error(f"[WalletService] {error_msg}")
                wallet_transaction.mark_as_failed(error_msg)
                
                return {
                    'success': False,
                    'transaction_reference': wallet_transaction.reference,
                    'message': error_msg
                }
            
            # Mettre à jour la transaction avec les infos FreeMoPay
            wallet_transaction.freemopay_reference = reference
            wallet_transaction.freemopay_external_id = freemopay_result.get('external_id', wallet_transaction.reference)
            wallet_transaction.status = 'processing'
            wallet_transaction.save()
            
            logger.info(f"[WalletService] Paiement initié avec succès - Référence: {reference}")
            
            # NOUVEAU: Faire le polling pour obtenir le statut final (comme dans payment.py)
            logger.info(f"[WalletService] Début du polling pour la référence: {reference}")
            polling_result = FreemoPayDirect.poll_payment_status(
                reference=reference,
                max_duration=120,  # 2 minutes comme dans payment.py
                interval=1  # 1 seconde comme dans payment.py
            )
            
            logger.info(f"[WalletService] Résultat du polling: {polling_result.get('status')} après {polling_result.get('attempts', 0)} tentatives")
            
            # Déterminer le statut final de la transaction
            polling_status = polling_result.get('status')
            final_freemo_status = polling_result.get('final_status')
            
            if polling_status == 'SUCCESS':
                # Paiement confirmé, créditer le wallet
                logger.info(f"[WalletService] ✅ Paiement confirmé avec succès")
                with transaction.atomic():
                    wallet = Wallet.objects.select_for_update().get(
                        user_type=wallet_transaction.user_type,
                        user_id=wallet_transaction.user_id
                    )
                    
                    # Mettre à jour le solde
                    new_balance = wallet.balance + wallet_transaction.amount
                    wallet.balance = new_balance
                    wallet.save()
                    
                    # Mettre à jour la transaction
                    wallet_transaction.balance_after = new_balance
                    wallet_transaction.mark_as_completed()
                    wallet_transaction.metadata.update({
                        'freemopay_polling_result': polling_result,
                        'completed_at': timezone.now().isoformat()
                    })
                    wallet_transaction.save()
                
                return {
                    'success': True,
                    'transaction_reference': wallet_transaction.reference,
                    'freemopay_reference': reference,
                    'amount': amount,
                    'status': 'completed',
                    'message': 'Dépôt effectué avec succès',
                    'new_balance': float(new_balance),
                    'polling_result': {
                        'final_status': polling_result.get('final_status'),
                        'reason': polling_result.get('reason'),
                        'duration': polling_result.get('polling_duration'),
                        'attempts': polling_result.get('attempts')
                    }
                }
                
            elif polling_status == 'FAILED':
                # Paiement échoué
                error_message = polling_result.get('reason', 'Paiement échoué')
                logger.warning(f"[WalletService] ❌ Paiement échoué/annulé - Raison: {error_message}")
                
                wallet_transaction.mark_as_failed(error_message)
                wallet_transaction.metadata.update({
                    'freemopay_polling_result': polling_result
                })
                wallet_transaction.save()
                
                return {
                    'success': False,
                    'transaction_reference': wallet_transaction.reference,
                    'freemopay_reference': reference,
                    'amount': amount,
                    'status': 'failed',
                    'message': f'Paiement échoué: {error_message}',
                    'polling_result': {
                        'final_status': polling_result.get('final_status'),
                        'reason': polling_result.get('reason'),
                        'duration': polling_result.get('polling_duration'),
                        'attempts': polling_result.get('attempts')
                    }
                }
                
            elif polling_status == 'TIMEOUT':
                # Timeout
                error_message = 'Timeout - Paiement non confirmé dans les délais'
                logger.warning(f"[WalletService] ⏱️ Timeout du paiement après {polling_result.get('polling_duration')}s")
                
                wallet_transaction.status = 'failed'
                wallet_transaction.error_message = error_message
                wallet_transaction.metadata.update({
                    'freemopay_polling_result': polling_result
                })
                wallet_transaction.save()
                
                return {
                    'success': False,
                    'transaction_reference': wallet_transaction.reference,
                    'freemopay_reference': reference,
                    'amount': amount,
                    'status': 'timeout',
                    'message': error_message,
                    'polling_result': {
                        'final_status': polling_result.get('final_status'),
                        'reason': polling_result.get('reason'),
                        'duration': polling_result.get('polling_duration'),
                        'attempts': polling_result.get('attempts')
                    }
                }
            else:
                # Statut inconnu
                error_message = f'Statut inconnu: {polling_status}'
                logger.error(f"[WalletService] Statut inconnu: {polling_status}")
                
                wallet_transaction.mark_as_failed(error_message)
                wallet_transaction.metadata.update({
                    'freemopay_polling_result': polling_result
                })
                wallet_transaction.save()
                
                return {
                    'success': False,
                    'transaction_reference': wallet_transaction.reference,
                    'freemopay_reference': reference,
                    'amount': amount,
                    'status': 'failed',
                    'message': error_message,
                    'polling_result': {
                        'final_status': polling_result.get('final_status'),
                        'reason': polling_result.get('reason'),
                        'duration': polling_result.get('polling_duration'),
                        'attempts': polling_result.get('attempts')
                    }
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de l'initiation du dépôt: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Erreur interne: {str(e)}'
            }
    
    @staticmethod
    def initiate_withdrawal(
        user, 
        user_type: str, 
        amount: Decimal, 
        phone_number: str,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Initier un retrait d'argent du wallet
        """
        try:
            # Obtenir le wallet
            wallet = WalletService.get_or_create_wallet(user, user_type)
            
            # Vérifier le solde
            if wallet.balance < amount:
                return {
                    'success': False,
                    'message': f'Solde insuffisant. Solde disponible: {wallet.balance} FCFA'
                }
            
            content_type = WalletService.get_content_type_for_user(user_type)
            
            # Créer la transaction en attente
            with transaction.atomic():
                # Bloquer temporairement le montant
                wallet.balance -= amount
                wallet.save()
                
                wallet_transaction = WalletTransaction.objects.create(
                    user_type=content_type,
                    user_id=user.id,
                    transaction_type='withdrawal',
                    amount=amount,
                    status='pending',
                    payment_method='mobile_money',
                    phone_number=phone_number,
                    balance_before=wallet.balance + amount,
                    balance_after=wallet.balance,
                    description=description or f"Retrait de {amount} FCFA",
                    metadata={
                        'user_type': user_type,
                        'phone_number': phone_number,
                        'initiated_at': timezone.now().isoformat()
                    }
                )
            
            # Appeler l'API FreeMoPay pour initier le retrait
            from .freemopay import FreemoPayDirect
            
            # Préparer les paramètres du retrait
            callback_url = "https://webhook.site/048fef35-a7ce-4ee2-bee1-e7b0d2be0c2a"  # URL temporaire
            
            freemopay_response = FreemoPayDirect.init_withdrawal(
                receiver=phone_number,
                amount=int(amount),  # Convertir en entier
                external_id=wallet_transaction.reference,
                callback=callback_url
            )
            
            logger.info(f"Réponse FreeMoPay pour retrait {wallet_transaction.reference}: {freemopay_response}")
            
            if freemopay_response.get('status') in ['CREATED', 'SUCCESS']:
                # Retrait initié avec succès
                freemopay_reference = freemopay_response.get('reference')
                wallet_transaction.freemopay_reference = freemopay_reference
                wallet_transaction.status = 'processing'
                wallet_transaction.metadata.update({
                    'freemopay_response': freemopay_response,
                    'freemopay_reference': freemopay_reference,
                    'processing_started_at': timezone.now().isoformat()
                })
                wallet_transaction.save()
                
                logger.info(f"Retrait FreeMoPay initié: {freemopay_reference} pour transaction {wallet_transaction.reference}")
                
                return {
                    'success': True,
                    'transaction_reference': wallet_transaction.reference,
                    'freemopay_reference': freemopay_reference,
                    'amount': amount,
                    'status': 'processing',
                    'message': 'Retrait en cours de traitement',
                    'new_balance': wallet.balance
                }
            else:
                # Erreur dans l'initiation du retrait FreeMoPay
                error_msg = freemopay_response.get('message', 'Erreur inconnue de FreeMoPay')
                logger.error(f"Erreur FreeMoPay pour retrait {wallet_transaction.reference}: {error_msg}")
                
                # Remettre le montant dans le wallet
                wallet.balance += amount
                wallet.save()
                
                # Marquer la transaction comme échouée
                wallet_transaction.status = 'failed'
                wallet_transaction.error_message = f"Erreur FreeMoPay: {error_msg}"
                wallet_transaction.metadata.update({
                    'freemopay_error': freemopay_response,
                    'failed_at': timezone.now().isoformat()
                })
                wallet_transaction.save()
                
                return {
                    'success': False,
                    'transaction_reference': wallet_transaction.reference,
                    'message': f'Erreur lors du retrait: {error_msg}',
                    'balance_restored': True
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de l'initiation du retrait: {str(e)}", exc_info=True)
            
            # Remettre le montant dans le wallet si erreur
            try:
                if 'wallet' in locals():
                    wallet.balance += amount
                    wallet.save()
            except:
                pass
                
            return {
                'success': False,
                'message': f'Erreur interne: {str(e)}'
            }
    
    
    @staticmethod
    def get_transaction_history(
        user, 
        user_type: str, 
        page: int = 1, 
        page_size: int = 20,
        transaction_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtenir l'historique des transactions d'un utilisateur
        """
        try:
            content_type = WalletService.get_content_type_for_user(user_type)
            
            # Base queryset
            queryset = WalletTransaction.objects.filter(
                user_type=content_type,
                user_id=user.id
            )
            
            # Filtrer par type si spécifié
            if transaction_type:
                queryset = queryset.filter(transaction_type=transaction_type)
            
            # Pagination
            offset = (page - 1) * page_size
            transactions = queryset[offset:offset + page_size]
            total_count = queryset.count()
            
            # Sérialiser les transactions
            transactions_data = []
            for tx in transactions:
                transactions_data.append({
                    'id': tx.id,
                    'reference': tx.reference,
                    'type': tx.transaction_type,
                    'type_display': tx.get_transaction_type_display(),
                    'amount': float(tx.amount),
                    'status': tx.status,
                    'status_display': tx.get_status_display(),
                    'payment_method': tx.payment_method,
                    'phone_number': tx.phone_number,
                    'description': tx.description,
                    'balance_before': float(tx.balance_before),
                    'balance_after': float(tx.balance_after),
                    'created_at': tx.created_at.isoformat(),
                    'completed_at': tx.completed_at.isoformat() if tx.completed_at else None,
                    'error_message': tx.error_message
                })
            
            # Obtenir le solde actuel
            current_balance = WalletService.get_wallet_balance(user, user_type)
            
            return {
                'success': True,
                'transactions': transactions_data,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size
                },
                'current_balance': float(current_balance)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'historique: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Erreur interne: {str(e)}'
            }
    
    @staticmethod
    def get_transaction_by_reference(reference: str) -> Optional[WalletTransaction]:
        """Obtenir une transaction par sa référence"""
        try:
            return WalletTransaction.objects.get(reference=reference)
        except WalletTransaction.DoesNotExist:
            return None