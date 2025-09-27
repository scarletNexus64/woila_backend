# EXISTING ENDPOINTS - DO NOT MODIFY URLs - Already integrated in production
# Wallet views migrated from api.viewsets.wallet

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal, InvalidOperation
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
from rest_framework import serializers
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from django.utils import timezone
import logging

# Import from api app (legacy)
from applications.users.models import UserDriver, UserCustomer
from applications.authentication.models import Token
from .models import WalletTransaction, Wallet
from applications.wallet.services.wallet_service import WalletService

logger = logging.getLogger(__name__)


def get_user_from_token(request):
    """Helper function to get user from authorization token"""
    auth_header = request.META.get('HTTP_AUTHORIZATION')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None, Response({
            'success': False,
            'message': 'Token d\'authentification manquant'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    token_value = auth_header[7:]  # Remove 'Bearer ' prefix
    try:
        token_obj = Token.objects.get(token=token_value, is_active=True)
        if token_obj.user_type == 'driver':
            user = UserDriver.objects.get(id=token_obj.user_id)
        else:
            user = UserCustomer.objects.get(id=token_obj.user_id)
        return user, None
    except Token.DoesNotExist:
        return None, Response({
            'success': False,
            'message': 'Token invalide'
        }, status=status.HTTP_401_UNAUTHORIZED)
    except (UserDriver.DoesNotExist, UserCustomer.DoesNotExist):
        return None, Response({
            'success': False,
            'message': 'Utilisateur introuvable'
        }, status=status.HTTP_404_NOT_FOUND)


# Serializers pour la documentation Swagger
class WalletDepositRequestSerializer(serializers.Serializer):
    """Serializer pour les requêtes de dépôt"""
    amount = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text="Montant à déposer en FCFA (exemple: 10000.00)",
        required=True
    )
    phone_number = serializers.CharField(
        max_length=15,
        help_text="Numéro de téléphone Mobile Money (exemple: +237690000000)",
        required=True
    )
    description = serializers.CharField(
        max_length=255,
        help_text="Description optionnelle du dépôt (exemple: Rechargement wallet)",
        required=False,
        allow_blank=True
    )


class WalletWithdrawalRequestSerializer(serializers.Serializer):
    """Serializer pour les requêtes de retrait"""
    amount = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text="Montant à retirer en FCFA (exemple: 5000.00)",
        required=True
    )
    phone_number = serializers.CharField(
        max_length=15,
        help_text="Numéro de téléphone Mobile Money pour recevoir l'argent (exemple: +237690000000)",
        required=True
    )
    description = serializers.CharField(
        max_length=255,
        help_text="Description optionnelle du retrait (exemple: Retrait vers Mobile Money)",
        required=False,
        allow_blank=True
    )


@method_decorator(csrf_exempt, name='dispatch')
class WalletBalanceView(APIView):
    """
    EXISTING ENDPOINT: GET /api/wallet/balance/
    DO NOT MODIFY - Already integrated in production
    """
    
    @extend_schema(
        operation_id="wallet_get_balance",
        summary="💰 Consulter le solde",
        description="Obtenir le solde du wallet de l'utilisateur connecté",
        responses={
            200: {
                'description': 'Solde récupéré avec succès',
                'example': {
                    'success': True,
                    'balance': 25000.00,
                    'user_type': 'driver',
                    'user_id': 1
                }
            },
            401: {'description': 'Non autorisé'},
            500: {'description': 'Erreur serveur'}
        },
        tags=['🏦 Wallet / Portefeuille']
    )
    def get(self, request):
        try:
            # Obtenir l'utilisateur depuis le token
            user, auth_error = get_user_from_token(request)
            if auth_error:
                return auth_error
            
            # Récupérer le solde
            balance = WalletService.get_balance(user)
            
            return Response({
                'success': True,
                'balance': balance,
                'user_type': 'driver' if isinstance(user, UserDriver) else 'customer',
                'user_id': user.id
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du solde: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de la récupération du solde'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class WalletDepositView(APIView):
    """
    EXISTING ENDPOINT: POST /api/wallet/deposit/
    DO NOT MODIFY - Already integrated in production
    """
    
    @extend_schema(
        operation_id="wallet_deposit",
        summary="💳 Effectuer un dépôt",
        description="Déposer de l'argent dans le wallet via Mobile Money",
        request=WalletDepositRequestSerializer,
        responses={
            200: {
                'description': 'Dépôt réussi',
                'example': {
                    'success': True,
                    'transaction_reference': 'TXN-20241225-001',
                    'freemopay_reference': 'FMP-12345',
                    'amount': 10000.00,
                    'status': 'completed',
                    'message': 'Dépôt effectué avec succès'
                }
            },
            400: {'description': 'Données invalides'},
            401: {'description': 'Non autorisé'},
            500: {'description': 'Erreur serveur'}
        },
        tags=['🏦 Wallet / Portefeuille']
    )
    def post(self, request):
        try:
            # Obtenir l'utilisateur depuis le token
            user, auth_error = get_user_from_token(request)
            if auth_error:
                return auth_error
            
            # Valider les données
            amount_str = request.data.get('amount')
            phone_number = request.data.get('phone_number')
            description = request.data.get('description', 'Dépôt wallet')
            
            if not amount_str or not phone_number:
                return Response({
                    'success': False,
                    'message': 'Montant et numéro de téléphone requis'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                amount = Decimal(str(amount_str))
            except (InvalidOperation, ValueError):
                return Response({
                    'success': False,
                    'message': 'Montant invalide'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if amount <= 0:
                return Response({
                    'success': False,
                    'message': 'Le montant doit être positif'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Effectuer le dépôt
            result = WalletService.deposit(
                user=user,
                amount=amount,
                phone_number=phone_number,
                description=description
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors du dépôt: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors du dépôt'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class WalletWithdrawalView(APIView):
    """
    EXISTING ENDPOINT: POST /api/wallet/withdrawal/
    DO NOT MODIFY - Already integrated in production
    """
    
    @extend_schema(
        operation_id="wallet_withdrawal",
        summary="💸 Effectuer un retrait",
        description="Retirer de l'argent du wallet vers Mobile Money",
        request=WalletWithdrawalRequestSerializer,
        responses={
            200: {
                'description': 'Retrait réussi',
                'example': {
                    'success': True,
                    'transaction_reference': 'TXN-20241225-002',
                    'amount': 5000.00,
                    'status': 'completed',
                    'message': 'Retrait effectué avec succès',
                    'new_balance': 20000.00
                }
            },
            400: {'description': 'Données invalides'},
            401: {'description': 'Non autorisé'},
            500: {'description': 'Erreur serveur'}
        },
        tags=['🏦 Wallet / Portefeuille']
    )
    def post(self, request):
        try:
            # Obtenir l'utilisateur depuis le token
            user, auth_error = get_user_from_token(request)
            if auth_error:
                return auth_error
            
            # Valider les données
            amount_str = request.data.get('amount')
            phone_number = request.data.get('phone_number')
            description = request.data.get('description', 'Retrait wallet')
            
            if not amount_str or not phone_number:
                return Response({
                    'success': False,
                    'message': 'Montant et numéro de téléphone requis'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                amount = Decimal(str(amount_str))
            except (InvalidOperation, ValueError):
                return Response({
                    'success': False,
                    'message': 'Montant invalide'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if amount <= 0:
                return Response({
                    'success': False,
                    'message': 'Le montant doit être positif'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Effectuer le retrait
            result = WalletService.withdraw(
                user=user,
                amount=amount,
                phone_number=phone_number,
                description=description
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors du retrait: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors du retrait'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class WalletTransactionHistoryView(APIView):
    """
    EXISTING ENDPOINT: GET /api/wallet/transactions/
    DO NOT MODIFY - Already integrated in production
    """
    
    @extend_schema(
        operation_id="wallet_transaction_history",
        summary="📋 Historique des transactions",
        description="Obtenir l'historique paginé des transactions du wallet",
        parameters=[
            OpenApiParameter(
                name='page',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Numéro de page (défaut: 1)',
                default=1
            ),
            OpenApiParameter(
                name='page_size',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Nombre d\'éléments par page (défaut: 10)',
                default=10
            ),
            OpenApiParameter(
                name='transaction_type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Type de transaction (deposit, withdrawal, etc.)',
                required=False
            )
        ],
        responses={
            200: {
                'description': 'Historique récupéré avec succès',
                'example': {
                    'success': True,
                    'transactions': [],
                    'pagination': {
                        'page': 1,
                        'page_size': 10,
                        'total_count': 25,
                        'total_pages': 3
                    },
                    'current_balance': 25000.00
                }
            },
            401: {'description': 'Non autorisé'},
            500: {'description': 'Erreur serveur'}
        },
        tags=['🏦 Wallet / Portefeuille']
    )
    def get(self, request):
        try:
            # Obtenir l'utilisateur depuis le token
            user, auth_error = get_user_from_token(request)
            if auth_error:
                return auth_error
            
            # Paramètres de pagination
            page = int(request.query_params.get('page', 1))
            page_size = min(int(request.query_params.get('page_size', 10)), 50)  # Max 50
            transaction_type = request.query_params.get('transaction_type')
            
            # Récupérer l'historique
            result = WalletService.get_transaction_history(
                user=user,
                page=page,
                page_size=page_size,
                transaction_type=transaction_type
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except ValueError:
            return Response({
                'success': False,
                'message': 'Paramètres de pagination invalides'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'historique: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de la récupération de l\'historique'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class WalletTransactionDetailView(APIView):
    """
    EXISTING ENDPOINT: GET /api/wallet/transactions/{reference}/
    DO NOT MODIFY - Already integrated in production
    """
    
    @extend_schema(
        operation_id="wallet_transaction_detail",
        summary="🔍 Détails d'une transaction",
        description="Obtenir les détails d'une transaction spécifique",
        responses={
            200: {
                'description': 'Détails récupérés avec succès',
                'example': {
                    'success': True,
                    'transaction': {
                        'id': 1,
                        'reference': 'TXN-20241225-001',
                        'type': 'deposit',
                        'amount': 10000.00,
                        'status': 'completed'
                    }
                }
            },
            401: {'description': 'Non autorisé'},
            404: {'description': 'Transaction introuvable'},
            500: {'description': 'Erreur serveur'}
        },
        tags=['🏦 Wallet / Portefeuille']
    )
    def get(self, request, reference):
        try:
            # Obtenir l'utilisateur depuis le token
            user, auth_error = get_user_from_token(request)
            if auth_error:
                return auth_error
            
            # Récupérer les détails de la transaction
            result = WalletService.get_transaction_detail(user=user, reference=reference)
            
            if not result['success']:
                return Response(result, status=status.HTTP_404_NOT_FOUND)
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des détails: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de la récupération des détails'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class WalletTransactionStatusView(APIView):
    """
    EXISTING ENDPOINT: GET /api/wallet/transactions/{reference}/check-status/
    DO NOT MODIFY - Already integrated in production
    """
    
    @extend_schema(
        operation_id="wallet_transaction_status",
        summary="🔄 Vérifier le statut d'une transaction",
        description="Vérifier et mettre à jour le statut d'une transaction avec FreeMoPay",
        responses={
            200: {
                'description': 'Statut vérifié avec succès',
                'example': {
                    'success': True,
                    'transaction': {},
                    'freemopay_status': {},
                    'status_updated': True,
                    'wallet_credited': True,
                    'new_balance': 30000.00
                }
            },
            401: {'description': 'Non autorisé'},
            404: {'description': 'Transaction introuvable'},
            500: {'description': 'Erreur serveur'}
        },
        tags=['🏦 Wallet / Portefeuille']
    )
    def get(self, request, reference):
        try:
            # Obtenir l'utilisateur depuis le token
            user, auth_error = get_user_from_token(request)
            if auth_error:
                return auth_error
            
            # Vérifier le statut de la transaction
            result = WalletService.check_transaction_status(user=user, reference=reference)
            
            if not result['success']:
                return Response(result, status=status.HTTP_404_NOT_FOUND)
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du statut: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de la vérification du statut'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)