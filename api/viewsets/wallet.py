from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal, InvalidOperation
from django.contrib.contenttypes.models import ContentType
import logging

from ..models import UserDriver, UserCustomer, Token, WalletTransaction, Wallet
from ..services.wallet_service import WalletService
from django.db import transaction
from rest_framework import serializers
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.openapi import AutoSchema  
from drf_spectacular.types import OpenApiTypes
from django.utils import timezone

logger = logging.getLogger(__name__)


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


class WalletBalanceResponseSerializer(serializers.Serializer):
    """Serializer pour les réponses de solde"""
    success = serializers.BooleanField(help_text="Indique si l'opération a réussi")
    balance = serializers.DecimalField(max_digits=10, decimal_places=2, help_text="Solde actuel en FCFA")
    user_type = serializers.CharField(help_text="Type d'utilisateur (driver ou customer)")
    user_id = serializers.IntegerField(help_text="ID de l'utilisateur")


class WalletDepositResponseSerializer(serializers.Serializer):
    """Serializer pour les réponses de dépôt"""
    success = serializers.BooleanField(help_text="Indique si l'opération a réussi")
    transaction_reference = serializers.CharField(help_text="Référence unique de la transaction")
    freemopay_reference = serializers.CharField(help_text="Référence FreeMoPay", required=False)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, help_text="Montant déposé")
    status = serializers.CharField(help_text="Statut de la transaction (completed, failed, processing, timeout)")
    message = serializers.CharField(help_text="Message descriptif")
    final_result = serializers.DictField(help_text="Résultat détaillé du polling FreeMoPay", required=False)


class WalletWithdrawalResponseSerializer(serializers.Serializer):
    """Serializer pour les réponses de retrait"""
    success = serializers.BooleanField(help_text="Indique si l'opération a réussi")
    transaction_reference = serializers.CharField(help_text="Référence unique de la transaction")
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, help_text="Montant retiré")
    status = serializers.CharField(help_text="Statut de la transaction")
    message = serializers.CharField(help_text="Message descriptif")
    new_balance = serializers.DecimalField(max_digits=10, decimal_places=2, help_text="Nouveau solde après retrait")


class TransactionSerializer(serializers.Serializer):
    """Serializer pour les transactions"""
    id = serializers.IntegerField(help_text="ID unique de la transaction")
    reference = serializers.CharField(help_text="Référence unique de la transaction")
    type = serializers.CharField(help_text="Type de transaction (deposit, withdrawal, etc.)")
    type_display = serializers.CharField(help_text="Libellé du type de transaction")
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, help_text="Montant de la transaction")
    status = serializers.CharField(help_text="Statut de la transaction")
    status_display = serializers.CharField(help_text="Libellé du statut")
    payment_method = serializers.CharField(help_text="Méthode de paiement utilisée", required=False)
    phone_number = serializers.CharField(help_text="Numéro de téléphone associé", required=False)
    description = serializers.CharField(help_text="Description de la transaction", required=False)
    balance_before = serializers.DecimalField(max_digits=10, decimal_places=2, help_text="Solde avant transaction")
    balance_after = serializers.DecimalField(max_digits=10, decimal_places=2, help_text="Solde après transaction")
    created_at = serializers.DateTimeField(help_text="Date de création")
    completed_at = serializers.DateTimeField(help_text="Date de completion", required=False, allow_null=True)
    error_message = serializers.CharField(help_text="Message d'erreur s'il y en a une", required=False, allow_null=True)


class PaginationSerializer(serializers.Serializer):
    """Serializer pour la pagination"""
    page = serializers.IntegerField(help_text="Numéro de la page actuelle")
    page_size = serializers.IntegerField(help_text="Nombre d'éléments par page")
    total_count = serializers.IntegerField(help_text="Nombre total d'éléments")
    total_pages = serializers.IntegerField(help_text="Nombre total de pages")


class WalletHistoryResponseSerializer(serializers.Serializer):
    """Serializer pour les réponses d'historique"""
    success = serializers.BooleanField(help_text="Indique si l'opération a réussi")
    transactions = TransactionSerializer(many=True, help_text="Liste des transactions")
    pagination = PaginationSerializer(help_text="Informations de pagination")
    current_balance = serializers.DecimalField(max_digits=10, decimal_places=2, help_text="Solde actuel")


class WalletTransactionDetailResponseSerializer(serializers.Serializer):
    """Serializer pour les détails d'une transaction"""
    success = serializers.BooleanField(help_text="Indique si l'opération a réussi")
    transaction = serializers.DictField(help_text="Détails complets de la transaction")


class ErrorResponseSerializer(serializers.Serializer):
    """Serializer pour les réponses d'erreur"""
    success = serializers.BooleanField(default=False, help_text="Toujours false en cas d'erreur")
    message = serializers.CharField(help_text="Message d'erreur descriptif")


class TransactionStatusResponseSerializer(serializers.Serializer):
    """Serializer pour la réponse de vérification de statut de transaction"""
    success = serializers.BooleanField(help_text="Indique si l'opération a réussi")
    transaction = serializers.DictField(help_text="Détails de la transaction")
    freemopay_status = serializers.DictField(help_text="Statut FreeMoPay", required=False)
    status_updated = serializers.BooleanField(help_text="Indique si le statut a été mis à jour")
    wallet_credited = serializers.BooleanField(help_text="Indique si le wallet a été crédité", required=False)
    new_balance = serializers.DecimalField(max_digits=10, decimal_places=2, help_text="Nouveau solde", required=False)


class WalletBalanceView(APIView):
    """
    API pour obtenir le solde du wallet de l'utilisateur connecté
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        operation_id="wallet_get_balance",
        summary="💰 Consulter le solde",
        description="Obtenir le solde du wallet de l'utilisateur connecté",
        responses={
            200: WalletBalanceResponseSerializer,
            401: ErrorResponseSerializer,
            500: ErrorResponseSerializer
        },
        tags=['🏦 Wallet / Portefeuille']
    )
    def get(self, request):
        try:
            # Obtenir l'utilisateur et son type depuis le token
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token_str = auth_header.replace('Bearer ', '')
            else:
                # Support pour le cas où le token est envoyé directement (sans Bearer)
                token_str = auth_header
            try:
                token_obj = Token.objects.get(token=token_str, is_active=True)
            except Token.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Token invalide'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Obtenir l'utilisateur
            if token_obj.user_type == 'driver':
                user = UserDriver.objects.get(id=token_obj.user_id)
            else:
                user = UserCustomer.objects.get(id=token_obj.user_id)
            
            # Obtenir le solde
            balance = WalletService.get_wallet_balance(user, token_obj.user_type)
            
            return Response({
                'success': True,
                'balance': float(balance),
                'user_type': token_obj.user_type,
                'user_id': token_obj.user_id
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du solde: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur interne du serveur'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WalletDepositView(APIView):
    """
    API pour initier un dépôt d'argent dans le wallet
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        operation_id="wallet_deposit",
        summary="📥 Déposer de l'argent",
        description="Initier un dépôt d'argent dans le wallet via Mobile Money (FreeMoPay). Le système fait du polling automatique pendant 2 minutes maximum pour confirmer le paiement.",
        request=WalletDepositRequestSerializer,
        responses={
            200: WalletDepositResponseSerializer,
            400: ErrorResponseSerializer,
            401: ErrorResponseSerializer,
            500: ErrorResponseSerializer
        },
        examples=[
            OpenApiExample(
                "Exemple de dépôt",
                summary="Dépôt de 10,000 FCFA",
                description="Exemple de requête pour déposer 10,000 FCFA",
                value={
                    "amount": 10000.00,
                    "phone_number": "+237690000000",
                    "description": "Rechargement wallet"
                }
            )
        ],
        tags=['🏦 Wallet / Portefeuille']
    )
    def post(self, request):
        try:
            # Obtenir l'utilisateur et son type depuis le token
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token_str = auth_header.replace('Bearer ', '')
            else:
                # Support pour le cas où le token est envoyé directement (sans Bearer)
                token_str = auth_header
            try:
                token_obj = Token.objects.get(token=token_str, is_active=True)
            except Token.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Token invalide'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Obtenir l'utilisateur
            if token_obj.user_type == 'driver':
                user = UserDriver.objects.get(id=token_obj.user_id)
            else:
                user = UserCustomer.objects.get(id=token_obj.user_id)
            
            # Valider les données
            data = request.data
            
            # Montant
            try:
                amount = Decimal(str(data.get('amount', 0)))
                if amount <= 0:
                    return Response({
                        'success': False,
                        'message': 'Le montant doit être supérieur à 0'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except (InvalidOperation, ValueError, TypeError):
                return Response({
                    'success': False,
                    'message': 'Montant invalide'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Numéro de téléphone
            phone_number = data.get('phone_number', '').strip()
            if not phone_number:
                return Response({
                    'success': False,
                    'message': 'Le numéro de téléphone est requis'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Description optionnelle
            description = data.get('description', '').strip()
            
            # Initier le dépôt
            result = WalletService.initiate_deposit(
                user=user,
                user_type=token_obj.user_type,
                amount=amount,
                phone_number=phone_number,
                description=description
            )
            
            if result['success']:
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Erreur lors de l'initiation du dépôt: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur interne du serveur'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WalletWithdrawalView(APIView):
    """
    API pour initier un retrait d'argent du wallet
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        operation_id="wallet_withdrawal",
        summary="📤 Retirer de l'argent",
        description="Initier un retrait d'argent du wallet vers Mobile Money. Le montant sera débité immédiatement du solde après vérification.",
        request=WalletWithdrawalRequestSerializer,
        responses={
            200: WalletWithdrawalResponseSerializer,
            400: ErrorResponseSerializer,
            401: ErrorResponseSerializer,
            500: ErrorResponseSerializer
        },
        examples=[
            OpenApiExample(
                "Exemple de retrait",
                summary="Retrait de 5,000 FCFA",
                description="Exemple de requête pour retirer 5,000 FCFA",
                value={
                    "amount": 5000.00,
                    "phone_number": "+237690000000",
                    "description": "Retrait vers Mobile Money"
                }
            )
        ],
        tags=['🏦 Wallet / Portefeuille']
    )
    def post(self, request):
        try:
            # Obtenir l'utilisateur et son type depuis le token
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token_str = auth_header.replace('Bearer ', '')
            else:
                # Support pour le cas où le token est envoyé directement (sans Bearer)
                token_str = auth_header
            try:
                token_obj = Token.objects.get(token=token_str, is_active=True)
            except Token.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Token invalide'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Obtenir l'utilisateur
            if token_obj.user_type == 'driver':
                user = UserDriver.objects.get(id=token_obj.user_id)
            else:
                user = UserCustomer.objects.get(id=token_obj.user_id)
            
            # Valider les données
            data = request.data
            
            # Montant
            try:
                amount = Decimal(str(data.get('amount', 0)))
                if amount <= 0:
                    return Response({
                        'success': False,
                        'message': 'Le montant doit être supérieur à 0'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except (InvalidOperation, ValueError, TypeError):
                return Response({
                    'success': False,
                    'message': 'Montant invalide'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Numéro de téléphone
            phone_number = data.get('phone_number', '').strip()
            if not phone_number:
                return Response({
                    'success': False,
                    'message': 'Le numéro de téléphone est requis'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Description optionnelle
            description = data.get('description', '').strip()
            
            # Initier le retrait
            result = WalletService.initiate_withdrawal(
                user=user,
                user_type=token_obj.user_type,
                amount=amount,
                phone_number=phone_number,
                description=description
            )
            
            if result['success']:
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Erreur lors de l'initiation du retrait: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur interne du serveur'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WalletTransactionHistoryView(APIView):
    """
    API pour obtenir l'historique des transactions du wallet
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        operation_id="wallet_transaction_history",
        summary="📋 Historique des transactions",
        description="Obtenir l'historique paginé des transactions du wallet de l'utilisateur connecté avec possibilité de filtrage par type",
        parameters=[
            OpenApiParameter(
                name='page',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Numéro de page (défaut: 1)",
                default=1,
                examples=[
                    OpenApiExample("Page 1", value=1),
                    OpenApiExample("Page 2", value=2)
                ]
            ),
            OpenApiParameter(
                name='page_size',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Nombre d'éléments par page (défaut: 20, max: 100)",
                default=20,
                examples=[
                    OpenApiExample("20 éléments", value=20),
                    OpenApiExample("50 éléments", value=50)
                ]
            ),
            OpenApiParameter(
                name='type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filtrer par type de transaction",
                enum=['deposit', 'withdrawal', 'transfer_in', 'transfer_out', 'refund', 'payment'],
                examples=[
                    OpenApiExample("Dépôts uniquement", value="deposit"),
                    OpenApiExample("Retraits uniquement", value="withdrawal")
                ]
            )
        ],
        responses={
            200: WalletHistoryResponseSerializer,
            400: ErrorResponseSerializer,
            401: ErrorResponseSerializer,
            500: ErrorResponseSerializer
        },
        tags=['🏦 Wallet / Portefeuille']
    )
    def get(self, request):
        try:
            # Obtenir l'utilisateur et son type depuis le token
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token_str = auth_header.replace('Bearer ', '')
            else:
                # Support pour le cas où le token est envoyé directement (sans Bearer)
                token_str = auth_header
            try:
                token_obj = Token.objects.get(token=token_str, is_active=True)
            except Token.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Token invalide'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Obtenir l'utilisateur
            if token_obj.user_type == 'driver':
                user = UserDriver.objects.get(id=token_obj.user_id)
            else:
                user = UserCustomer.objects.get(id=token_obj.user_id)
            
            # Paramètres de pagination et filtrage
            page = int(request.query_params.get('page', 1))
            page_size = min(int(request.query_params.get('page_size', 20)), 100)
            transaction_type = request.query_params.get('type')
            
            # Obtenir l'historique
            result = WalletService.get_transaction_history(
                user=user,
                user_type=token_obj.user_type,
                page=page,
                page_size=page_size,
                transaction_type=transaction_type
            )
            
            if result['success']:
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
        except ValueError:
            return Response({
                'success': False,
                'message': 'Paramètres de pagination invalides'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'historique: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur interne du serveur'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WalletTransactionDetailView(APIView):
    """
    API pour obtenir les détails d'une transaction spécifique
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        operation_id="wallet_transaction_detail",
        summary="🔍 Détails d'une transaction",
        description="Obtenir les détails complets d'une transaction spécifique par sa référence unique",
        parameters=[
            OpenApiParameter(
                name='reference',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="Référence unique de la transaction",
                required=True,
                examples=[
                    OpenApiExample("Dépôt", value="DEP-20231201123045-A1B2C3D4"),
                    OpenApiExample("Retrait", value="WIT-20231201140030-B5C6D7E8")
                ]
            )
        ],
        responses={
            200: WalletTransactionDetailResponseSerializer,
            404: ErrorResponseSerializer,
            401: ErrorResponseSerializer,
            500: ErrorResponseSerializer
        },
        tags=['🏦 Wallet / Portefeuille']
    )
    def get(self, request, reference):
        try:
            # Obtenir l'utilisateur et son type depuis le token
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token_str = auth_header.replace('Bearer ', '')
            else:
                # Support pour le cas où le token est envoyé directement (sans Bearer)
                token_str = auth_header
            try:
                token_obj = Token.objects.get(token=token_str, is_active=True)
            except Token.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Token invalide'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Obtenir la transaction
            try:
                content_type = WalletService.get_content_type_for_user(token_obj.user_type)
                transaction_obj = WalletTransaction.objects.get(
                    reference=reference,
                    user_type=content_type,
                    user_id=token_obj.user_id
                )
            except WalletTransaction.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Transaction non trouvée'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Sérialiser la transaction
            transaction_data = {
                'id': transaction_obj.id,
                'reference': transaction_obj.reference,
                'type': transaction_obj.transaction_type,
                'type_display': transaction_obj.get_transaction_type_display(),
                'amount': float(transaction_obj.amount),
                'status': transaction_obj.status,
                'status_display': transaction_obj.get_status_display(),
                'payment_method': transaction_obj.payment_method,
                'phone_number': transaction_obj.phone_number,
                'description': transaction_obj.description,
                'balance_before': float(transaction_obj.balance_before),
                'balance_after': float(transaction_obj.balance_after),
                'freemopay_reference': transaction_obj.freemopay_reference,
                'freemopay_external_id': transaction_obj.freemopay_external_id,
                'created_at': transaction_obj.created_at.isoformat(),
                'updated_at': transaction_obj.updated_at.isoformat(),
                'completed_at': transaction_obj.completed_at.isoformat() if transaction_obj.completed_at else None,
                'error_message': transaction_obj.error_message,
                'metadata': transaction_obj.metadata
            }
            
            return Response({
                'success': True,
                'transaction': transaction_data
            }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des détails: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur interne du serveur'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WalletTransactionStatusView(APIView):
    """
    API pour vérifier et mettre à jour le statut d'une transaction wallet
    en consultant directement FreeMoPay (utile si le polling a timeout)
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        operation_id="wallet_check_transaction_status",
        summary="🔄 Vérifier le statut d'une transaction",
        description="Vérifie le statut actuel d'une transaction auprès de FreeMoPay et met à jour le wallet si nécessaire",
        parameters=[
            OpenApiParameter(
                name='reference',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="Référence unique de la transaction wallet",
                required=True,
                examples=[
                    OpenApiExample("Transaction de dépôt", value="DEP-20231201123045-A1B2C3D4")
                ]
            )
        ],
        responses={
            200: TransactionStatusResponseSerializer,
            404: ErrorResponseSerializer,
            401: ErrorResponseSerializer,
            500: ErrorResponseSerializer
        },
        tags=['🏦 Wallet / Portefeuille']
    )
    def post(self, request, reference):
        try:
            # Obtenir l'utilisateur et son type depuis le token
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token_str = auth_header.replace('Bearer ', '')
            else:
                # Support pour le cas où le token est envoyé directement (sans Bearer)
                token_str = auth_header
                
            try:
                token_obj = Token.objects.get(token=token_str, is_active=True)
            except Token.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Token invalide'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Vérifier que la transaction appartient bien à l'utilisateur
            try:
                content_type = WalletService.get_content_type_for_user(token_obj.user_type)
                wallet_transaction = WalletTransaction.objects.get(
                    reference=reference,
                    user_type=content_type,
                    user_id=token_obj.user_id
                )
            except WalletTransaction.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Transaction non trouvée'
                }, status=status.HTTP_404_NOT_FOUND)
            
            logger.info(f"[WalletTransactionStatus] Vérification du statut pour transaction: {reference}")
            
            # Obtenir le statut actuel depuis FreeMoPay
            if not wallet_transaction.freemopay_reference:
                return Response({
                    'success': False,
                    'message': 'Pas de référence FreeMoPay disponible pour cette transaction'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérifier le statut chez FreeMoPay
            from ..services.freemopay import FreemoPayDirect
            freemopay_status = FreemoPayDirect.get_payment_status(wallet_transaction.freemopay_reference)
            freemo_status = freemopay_status.get('status')
            
            logger.info(f"[WalletTransactionStatus] Statut FreeMoPay: {freemo_status}")
            
            # Variables pour le retour
            status_updated = False
            wallet_credited = False
            new_balance = None
            old_status = wallet_transaction.status
            
            # Mettre à jour selon le statut FreeMoPay
            if freemo_status == 'SUCCESS' and wallet_transaction.status in ['pending', 'processing', 'failed']:
                # Paiement confirmé - créditer le wallet
                logger.info(f"[WalletTransactionStatus] Paiement confirmé - Crédit du wallet")
                
                with transaction.atomic():
                    # Obtenir le wallet
                    wallet = Wallet.objects.select_for_update().get(
                        user_type=wallet_transaction.user_type,
                        user_id=wallet_transaction.user_id
                    )
                    
                    # Créditer uniquement si pas déjà fait
                    if wallet_transaction.status != 'completed':
                        new_balance = wallet.balance + wallet_transaction.amount
                        wallet.balance = new_balance
                        wallet.save()
                        wallet_credited = True
                        
                        # Mettre à jour la transaction
                        wallet_transaction.balance_after = new_balance
                        wallet_transaction.mark_as_completed()
                        wallet_transaction.metadata.update({
                            'status_check_update': timezone.now().isoformat(),
                            'freemopay_final_status': freemopay_status
                        })
                        wallet_transaction.save()
                        status_updated = True
                        
                        logger.info(f"[WalletTransactionStatus] Wallet crédité: {wallet_transaction.amount} FCFA, nouveau solde: {new_balance}")
                    else:
                        new_balance = wallet.balance
                        
            elif freemo_status in ['FAILED', 'CANCELLED'] and wallet_transaction.status != 'failed':
                # Paiement échoué
                wallet_transaction.status = 'failed'
                wallet_transaction.error_message = freemopay_status.get('reason', 'Paiement échoué')
                wallet_transaction.save()
                status_updated = True
                logger.info(f"[WalletTransactionStatus] Statut mis à jour: {old_status} → failed")
            
            # Sérialiser la transaction mise à jour
            transaction_data = {
                'id': wallet_transaction.id,
                'reference': wallet_transaction.reference,
                'type': wallet_transaction.transaction_type,
                'amount': float(wallet_transaction.amount),
                'status': wallet_transaction.status,
                'balance_before': float(wallet_transaction.balance_before),
                'balance_after': float(wallet_transaction.balance_after),
                'created_at': wallet_transaction.created_at.isoformat(),
                'completed_at': wallet_transaction.completed_at.isoformat() if wallet_transaction.completed_at else None,
                'error_message': wallet_transaction.error_message
            }
            
            return Response({
                'success': True,
                'transaction': transaction_data,
                'freemopay_status': freemopay_status,
                'status_updated': status_updated,
                'wallet_credited': wallet_credited,
                'new_balance': float(new_balance) if new_balance is not None else None
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"[WalletTransactionStatus] Erreur lors de la vérification: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur interne du serveur'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)