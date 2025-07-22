"""
ViewSets pour le système de parrainage
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Sum

from ..models import ReferralCode, Wallet, GeneralConfig, UserDriver, UserCustomer
from ..serializers import (
    ReferralInfoSerializer, ValidateReferralCodeSerializer, 
    WalletBalanceSerializer, ReferralStatsSerializer
)


class ReferralViewSet(viewsets.ViewSet):
    """
    ViewSet pour gérer le système de parrainage
    """
    
    @action(detail=False, methods=['post'], url_path='validate-code')
    def validate_referral_code(self, request):
        """
        Valide un code de parrainage et retourne les informations
        
        POST /api/referral/validate-code/
        {
            "referral_code": "ABC12345"
        }
        """
        serializer = ValidateReferralCodeSerializer(data=request.data)
        
        if serializer.is_valid():
            response_data = serializer.to_representation(serializer.validated_data)
            return Response(response_data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='user-info')
    def user_referral_info(self, request):
        """
        Récupère les informations de parrainage d'un utilisateur
        
        GET /api/referral/user-info/?user_type=driver&user_id=123
        ou
        GET /api/referral/user-info/?phone_number=+223123456789&user_type=customer
        """
        user_type = request.query_params.get('user_type')  # 'driver' ou 'customer'
        user_id = request.query_params.get('user_id')
        phone_number = request.query_params.get('phone_number')
        
        if not user_type or user_type not in ['driver', 'customer']:
            return Response(
                {'error': 'user_type requis (driver ou customer)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Récupérer l'utilisateur
        try:
            if user_type == 'driver':
                if user_id:
                    user = UserDriver.objects.get(id=user_id, is_active=True)
                elif phone_number:
                    user = UserDriver.objects.get(phone_number=phone_number, is_active=True)
                else:
                    return Response(
                        {'error': 'user_id ou phone_number requis'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                content_type = ContentType.objects.get_for_model(UserDriver)
            else:  # customer
                if user_id:
                    user = UserCustomer.objects.get(id=user_id, is_active=True)
                elif phone_number:
                    user = UserCustomer.objects.get(phone_number=phone_number, is_active=True)
                else:
                    return Response(
                        {'error': 'user_id ou phone_number requis'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                content_type = ContentType.objects.get_for_model(UserCustomer)
                
        except (UserDriver.DoesNotExist, UserCustomer.DoesNotExist):
            return Response(
                {'error': 'Utilisateur introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Récupérer le code de parrainage
        try:
            referral_code = ReferralCode.objects.get(
                user_type=content_type,
                user_id=user.id
            )
        except ReferralCode.DoesNotExist:
            return Response(
                {'error': 'Code de parrainage introuvable pour cet utilisateur'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Récupérer le wallet
        try:
            wallet = Wallet.objects.get(
                user_type=content_type,
                user_id=user.id
            )
        except Wallet.DoesNotExist:
            return Response(
                {'error': 'Wallet introuvable pour cet utilisateur'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Récupérer le bonus de bienvenue
        try:
            bonus_config = GeneralConfig.objects.get(search_key='WELCOME_BONUS_AMOUNT', active=True)
            welcome_bonus = bonus_config.get_numeric_value() or 0
        except GeneralConfig.DoesNotExist:
            welcome_bonus = 0
        
        # Vérifier si le système de parrainage est actif
        try:
            referral_active_config = GeneralConfig.objects.get(search_key='ENABLE_REFERRAL_SYSTEM', active=True)
            referral_system_active = referral_active_config.get_boolean_value() or False
        except GeneralConfig.DoesNotExist:
            referral_system_active = True  # Par défaut actif
        
        response_data = {
            'referral_code': referral_code.code,
            'wallet_balance': wallet.balance,
            'welcome_bonus_amount': welcome_bonus,
            'referral_system_active': referral_system_active,
            'user_info': str(user),
            'user_type': user_type,
            'code_active': referral_code.is_active,
            'created_at': referral_code.created_at
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='wallet')
    def user_wallet(self, request):
        """
        Récupère le wallet d'un utilisateur
        
        GET /api/referral/wallet/?user_type=driver&user_id=123
        """
        user_type = request.query_params.get('user_type')
        user_id = request.query_params.get('user_id')
        
        if not all([user_type, user_id]):
            return Response(
                {'error': 'user_type et user_id requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if user_type not in ['driver', 'customer']:
            return Response(
                {'error': 'user_type doit être driver ou customer'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Récupérer le content type
        if user_type == 'driver':
            content_type = ContentType.objects.get_for_model(UserDriver)
        else:
            content_type = ContentType.objects.get_for_model(UserCustomer)
        
        try:
            wallet = Wallet.objects.get(
                user_type=content_type,
                user_id=user_id
            )
        except Wallet.DoesNotExist:
            return Response(
                {'error': 'Wallet introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = WalletBalanceSerializer(wallet)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='stats')
    def referral_stats(self, request):
        """
        Statistiques générales du système de parrainage
        
        GET /api/referral/stats/
        """
        # Compter les codes de parrainage
        total_referrals = ReferralCode.objects.count()
        active_referrals = ReferralCode.objects.filter(is_active=True).count()
        
        # Calculer le total des bonus distribués
        total_bonus_distributed = Wallet.objects.aggregate(
            total=Sum('balance')
        )['total'] or 0
        
        # Récupérer le montant du bonus de bienvenue
        try:
            bonus_config = GeneralConfig.objects.get(search_key='WELCOME_BONUS_AMOUNT', active=True)
            welcome_bonus_amount = bonus_config.get_numeric_value() or 0
        except GeneralConfig.DoesNotExist:
            welcome_bonus_amount = 0
        
        response_data = {
            'total_referrals': total_referrals,
            'active_referrals': active_referrals,
            'total_bonus_distributed': total_bonus_distributed,
            'welcome_bonus_amount': welcome_bonus_amount
        }
        
        return Response(response_data, status=status.HTTP_200_OK)