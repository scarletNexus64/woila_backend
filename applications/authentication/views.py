# EXISTING ENDPOINTS - DO NOT MODIFY URLs - Already integrated in production
# Authentication views migrated from api.viewsets

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema, OpenApiExample
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
import threading
import time

# Import from api app (legacy)
from .models import Token, OTPVerification, ReferralCode
from .serializers import LoginSerializer, LogoutSerializer
from applications.users.serializers import RegisterDriverSerializer, RegisterCustomerSerializer
from applications.users.models import UserDriver, UserCustomer
from applications.notifications.models import Notification
from applications.wallet.models import Wallet
from core.models import GeneralConfig
from applications.notifications.services.notification_service import NotificationService


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    """
    EXISTING ENDPOINT: POST /api/auth/login/
    DO NOT MODIFY - Already integrated in production
    """
    
    @extend_schema(
        tags=['Authentication'],
        summary='Connexion utilisateur',
        description='Permet aux chauffeurs et clients de se connecter avec leur numéro de téléphone et mot de passe',
        request=LoginSerializer,
        responses={
            200: {'description': 'Connexion réussie'},
            400: {'description': 'Données invalides'},
            401: {'description': 'Identifiants incorrects'},
        },
        examples=[
            OpenApiExample(
                'Driver Login',
                summary='Connexion chauffeur',
                description='Exemple de connexion pour un chauffeur',
                value={
                    'phone_number': '+33123456789',
                    'password': 'motdepasse123',
                    'user_type': 'driver'
                },
                request_only=True,
            ),
            OpenApiExample(
                'Customer Login', 
                summary='Connexion client',
                description='Exemple de connexion pour un client',
                value={
                    'phone_number': '+33987654321',
                    'password': 'motdepasse456',
                    'user_type': 'customer'
                },
                request_only=True,
            ),
            OpenApiExample(
                'Successful Response',
                summary='Réponse de succès',
                description='Token généré après connexion réussie',
                value={
                    'success': True,
                    'message': 'Connexion réussie',
                    'token': '550e8400-e29b-41d4-a716-446655440000',
                    'user_type': 'driver',
                    'user_id': 1,
                    'user_info': {
                        'id': 1,
                        'name': 'John',
                        'surname': 'Doe',
                        'phone_number': '+33123456789'
                    }
                },
                response_only=True,
            )
        ]
    )
    def post(self, request):
        """
        Connecter un utilisateur (chauffeur ou client)
        """
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            user_type = serializer.validated_data['user_type']
            
            # Désactiver les anciens tokens
            Token.objects.filter(
                user_type=user_type,
                user_id=user.id,
                is_active=True
            ).update(is_active=False)
            
            # Créer un nouveau token
            token = Token.objects.create(
                user_type=user_type,
                user_id=user.id
            )
            
            # Vérifier si c'est le premier login (pour envoyer notification de bienvenue)
            previous_tokens_count = Token.objects.filter(
                user_type=user_type,
                user_id=user.id
            ).exclude(id=token.id).count()
            
            if previous_tokens_count == 0:
                # C'est le premier login - Vérifier s'il n'a pas déjà reçu de notification de bienvenue
                content_type = ContentType.objects.get_for_model(user)
                welcome_notifications = Notification.objects.filter(
                    user_type=content_type,
                    user_id=user.id,
                    notification_type='welcome'
                ).exists()
                
                if not welcome_notifications:
                    # Envoyer notification de bienvenue après un délai de 2 secondes
                    def send_welcome_delayed():
                        time.sleep(2)  # Attendre 2 secondes
                        try:
                            NotificationService.send_welcome_notification(user)
                            print(f"📤 Notification de bienvenue envoyée à {user.name if hasattr(user, 'name') else f'Client {user.phone_number}'} lors du premier login")
                        except Exception as e:
                            print(f"❌ Erreur envoi notification bienvenue: {e}")
                    
                    thread = threading.Thread(target=send_welcome_delayed)
                    thread.daemon = True
                    thread.start()
            
            # Préparer les informations utilisateur
            if user_type == 'driver':
                user_info = {
                    'id': user.id,
                    'name': user.name,
                    'surname': user.surname,
                    'phone_number': user.phone_number,
                    'gender': user.gender,
                    'age': user.age,
                    'birthday': user.birthday.isoformat() if user.birthday else None
                }
            else:
                user_info = {
                    'id': user.id,
                    'phone_number': user.phone_number
                }
            
            return Response({
                'success': True,
                'message': 'Connexion réussie',
                'token': str(token.token),
                'user_type': user_type,
                'user_id': user.id,
                'user_info': user_info
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class RegisterDriverView(APIView):
    """
    EXISTING ENDPOINT: POST /api/auth/register/driver/
    DO NOT MODIFY - Already integrated in production
    """
    parser_classes = [MultiPartParser, FormParser]
    
    @extend_schema(
        tags=['Authentication'],
        summary='Inscription chauffeur',
        description='Permet à un nouveau chauffeur de s\'inscrire avec toutes ses informations personnelles',
        request=RegisterDriverSerializer,
        responses={
            201: {'description': 'Inscription réussie'},
            400: {'description': 'Données invalides'},
        },
        examples=[
            OpenApiExample(
                'Driver Registration',
                summary='Inscription chauffeur',
                description='Exemple d\'inscription pour un nouveau chauffeur',
                value={
                    'phone_number': '+33123456789',
                    'password': 'motdepasse123',
                    'confirm_password': 'motdepasse123',
                    'name': 'Jean',
                    'surname': 'Dupont',
                    'gender': 'M',
                    'age': 35,
                    'birthday': '1988-05-15',
                    'referral_code': 'REF12345'
                },
                request_only=True,
            ),
            OpenApiExample(
                'Successful Registration',
                summary='Inscription réussie',
                description='Réponse après inscription réussie du chauffeur',
                value={
                    'success': True,
                    'message': 'Inscription chauffeur réussie',
                    'user_type': 'driver',
                    'user_id': 1,
                    'user_info': {
                        'id': 1,
                        'name': 'Jean',
                        'surname': 'Dupont',
                        'phone_number': '+33123456789',
                        'gender': 'M',
                        'age': 35,
                        'birthday': '1988-05-15'
                    }
                },
                response_only=True,
            )
        ]
    )
    def post(self, request):
        """
        Inscrire un nouveau chauffeur
        """
        serializer = RegisterDriverSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    # Créer le chauffeur
                    driver = serializer.save()

                    # Créer le portefeuille et le code de parrainage
                    driver_content_type = ContentType.objects.get_for_model(driver)
                    Wallet.objects.get_or_create(
                        user_type=driver_content_type,
                        user_id=driver.id,
                        defaults={'balance': 0}
                    )
                    ReferralCode.objects.get_or_create(
                        user_type=driver_content_type,
                        user_id=driver.id
                    )
                    
                    # Préparer les informations du chauffeur
                    user_info = {
                        'id': driver.id,
                        'name': driver.name,
                        'surname': driver.surname,
                        'phone_number': driver.phone_number,
                        'gender': driver.gender,
                        'age': driver.age,
                        'birthday': driver.birthday.isoformat() if driver.birthday else None,
                        'profile_picture_url': driver.get_profile_picture_url(request) if driver.profile_picture else None
                    }
                    return Response({
                        'success': True,
                        'message': 'Inscription chauffeur réussie. Vous pouvez maintenant vous connecter.',
                        'user_type': 'driver',
                        'user_id': driver.id,
                        'user_info': user_info
                    }, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({
                    'success': False,
                    'errors': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class RegisterCustomerView(APIView):
    """
    EXISTING ENDPOINT: POST /api/auth/register/customer/
    DO NOT MODIFY - Already integrated in production
    """
    parser_classes = [MultiPartParser, FormParser]
    
    @extend_schema(
        tags=['Authentication'],
        summary='Inscription client',
        description='Permet à un nouveau client de s\'inscrire avec ses informations de base',
        request=RegisterCustomerSerializer,
        responses={
            201: {'description': 'Inscription réussie'},
            400: {'description': 'Données invalides'},
        },
        examples=[
            OpenApiExample(
                'Customer Registration',
                summary='Inscription client',
                description='Exemple d\'inscription pour un nouveau client',
                value={
                    'phone_number': '+33987654321',
                    'password': 'motdepasse456',
                    'confirm_password': 'motdepasse456',
                    'referral_code': 'REF54321'
                },
                request_only=True,
            ),
            OpenApiExample(
                'Successful Registration',
                summary='Inscription réussie',
                description='Réponse après inscription réussie du client',
                value={
                    'success': True,
                    'message': 'Inscription client réussie',
                    'user_type': 'customer',
                    'user_id': 1,
                    'user_info': {
                        'id': 1,
                        'phone_number': '+33987654321'
                    }
                },
                response_only=True,
            )
        ]
    )
    def post(self, request):
        """
        Inscrire un nouveau client
        """
        serializer = RegisterCustomerSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    # Créer le client
                    customer = serializer.save()

                    # Créer le portefeuille et le code de parrainage
                    customer_content_type = ContentType.objects.get_for_model(customer)
                    Wallet.objects.get_or_create(
                        user_type=customer_content_type,
                        user_id=customer.id,
                        defaults={'balance': 0}
                    )
                    ReferralCode.objects.get_or_create(
                        user_type=customer_content_type,
                        user_id=customer.id
                    )

                    # Préparer les informations du client
                    user_info = {
                        'id': customer.id,
                        'phone_number': customer.phone_number
                    }
                    return Response({
                        'success': True,
                        'message': 'Inscription client réussie. Vous pouvez maintenant vous connecter.',
                        'user_type': 'customer',
                        'user_id': customer.id,
                        'user_info': user_info
                    }, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({
                    'success': False,
                    'errors': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(APIView):
    """
    EXISTING ENDPOINT: POST /api/auth/logout/
    DO NOT MODIFY - Already integrated in production
    """
    
    @extend_schema(
        tags=['Authentication'],
        summary='Déconnexion utilisateur',
        description='Permet aux utilisateurs (chauffeurs et clients) de se déconnecter en désactivant leur token',
        request=LogoutSerializer,
        responses={
            200: {'description': 'Déconnexion réussie'},
            400: {'description': 'Token invalide'},
            404: {'description': 'Token non trouvé'},
        },
        examples=[
            OpenApiExample(
                'Logout Request',
                summary='Demande de déconnexion',
                description='Token à désactiver pour la déconnexion',
                value={
                    'token': '550e8400-e29b-41d4-a716-446655440000'
                },
                request_only=True,
            ),
            OpenApiExample(
                'Successful Logout',
                summary='Déconnexion réussie',
                description='Confirmation de déconnexion',
                value={
                    'success': True,
                    'message': 'Déconnexion réussie'
                },
                response_only=True,
            )
        ]
    )
    def post(self, request):
        """
        Déconnecter un utilisateur en désactivant son token
        """
        serializer = LogoutSerializer(data=request.data)
        
        if serializer.is_valid():
            token_value = serializer.validated_data['token']
            
            try:
                # Rechercher le token actif
                token = Token.objects.get(
                    token=token_value,
                    is_active=True
                )
                
                # Désactiver le token
                token.is_active = False
                token.save()
                
                return Response({
                    'success': True,
                    'message': 'Déconnexion réussie'
                }, status=status.HTTP_200_OK)
                
            except Token.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Token invalide ou déjà expiré'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class TokenVerifyView(APIView):
    """
    EXISTING ENDPOINT: POST /api/auth/token/verify/
    DO NOT MODIFY - Already integrated in production
    """
    def post(self, request):
        # Logic from api.viewsets.token
        pass


class TokenRefreshView(APIView):
    """
    EXISTING ENDPOINT: POST /api/auth/token/refresh/
    DO NOT MODIFY - Already integrated in production
    """
    def post(self, request):
        # Logic from api.viewsets.token
        pass


class ForgotPasswordView(APIView):
    """
    EXISTING ENDPOINT: POST /api/auth/forgot-password/
    DO NOT MODIFY - Already integrated in production
    """
    def post(self, request):
        # Logic from api.viewsets.forgot_password
        pass


class GenerateOTPView(APIView):
    """
    EXISTING ENDPOINT: POST /api/auth/generate-otp/
    DO NOT MODIFY - Already integrated in production
    """
    def post(self, request):
        # Logic from api.viewsets.otp
        pass


class VerifyOTPView(APIView):
    """
    EXISTING ENDPOINT: POST /api/auth/verify-otp/
    DO NOT MODIFY - Already integrated in production
    """
    def post(self, request):
        # Logic from api.viewsets.otp
        pass