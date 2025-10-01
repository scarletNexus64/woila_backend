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
        print(f"🚀 Starting driver registration")
        print(f"📋 Request data keys: {request.data.keys()}")

        serializer = RegisterDriverSerializer(data=request.data)

        if serializer.is_valid():
            try:
                print(f"✅ Serializer valid, creating driver...")
                with transaction.atomic():
                    # Créer le chauffeur (wallet et referral code créés automatiquement par le serializer)
                    driver = serializer.save()
                    print(f"✅ Driver created: ID={driver.id}, Phone={driver.phone_number}")

                    # Préparer les informations du chauffeur
                    print(f"📦 Preparing user info...")
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
                    print(f"✅ User info prepared successfully")
                    return Response({
                        'success': True,
                        'message': 'Inscription chauffeur réussie. Vous pouvez maintenant vous connecter.',
                        'user_type': 'driver',
                        'user_id': driver.id,
                        'user_info': user_info
                    }, status=status.HTTP_201_CREATED)

            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                print(f"❌❌❌ [REGISTRATION ERROR] ❌❌❌")
                print(error_trace)
                print(f"Error message: {str(e)}")

                return Response({
                    'success': False,
                    'error': str(e),
                    'message': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        print(f"❌ Serializer validation failed: {serializer.errors}")
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


@method_decorator(csrf_exempt, name='dispatch')
class GenerateOTPView(APIView):
    """
    EXISTING ENDPOINT: POST /api/auth/generate-otp/
    DO NOT MODIFY - Already integrated in production
    """

    @extend_schema(
        tags=['Authentication'],
        summary='Générer un code OTP',
        description='Génère un code OTP à 4 chiffres et l\'envoie par SMS',
        request={
            'type': 'object',
            'properties': {
                'phone_number': {'type': 'string', 'example': '+237690000000'},
                'user_type': {'type': 'string', 'enum': ['driver', 'customer']},
            },
            'required': ['phone_number', 'user_type']
        },
        responses={
            200: {'description': 'OTP généré avec succès'},
            400: {'description': 'Données invalides'},
        }
    )
    def post(self, request):
        """
        Générer un code OTP pour un utilisateur
        """
        from .serializers import GenerateOTPSerializer
        import random

        serializer = GenerateOTPSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Données invalides',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data['phone_number']
        user_type = serializer.validated_data['user_type']
        purpose = serializer.validated_data.get('purpose', 'forgot_password')

        # Vérifier si l'utilisateur existe
        if user_type == 'driver':
            user_exists = UserDriver.objects.filter(phone_number=phone_number).exists()
        else:
            user_exists = UserCustomer.objects.filter(phone_number=phone_number).exists()

        # Logique selon le but de l'OTP
        if purpose == 'register':
            # Pour l'inscription, le numéro NE DOIT PAS exister
            if user_exists:
                return Response({
                    'success': False,
                    'error': 'Ce numéro de téléphone est déjà utilisé'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Pour forgot_password, le numéro DOIT exister
            if not user_exists:
                return Response({
                    'success': False,
                    'error': 'Aucun utilisateur trouvé avec ce numéro'
                }, status=status.HTTP_404_NOT_FOUND)

        # Désactiver les anciens OTP pour ce numéro
        OTPVerification.objects.filter(
            phone_number=phone_number,
            user_type=user_type,
            is_verified=False
        ).update(is_verified=True)  # Marquer comme "utilisés"

        # Générer un code OTP à 4 chiffres (compatible avec l'app Flutter)
        otp_code = ''.join([str(random.randint(0, 9)) for _ in range(4)])

        # Créer l'OTP
        otp = OTPVerification.objects.create(
            phone_number=phone_number,
            otp_code=otp_code,
            user_type=user_type
        )

        print(f"✅ OTP created: code={otp.otp_code}, phone={otp.phone_number}, user_type={otp.user_type}, is_verified={otp.is_verified}, expires_at={otp.expires_at}")

        # Envoyer l'OTP via WhatsApp/SMS (en arrière-plan pour ne pas bloquer)
        def send_otp_async():
            try:
                result = NotificationService.send_otp(
                    recipient=phone_number,
                    otp_code=otp_code
                )
                if result['success']:
                    print(f"✅ OTP envoyé avec succès via {result.get('channel', 'unknown')}")
                else:
                    print(f"❌ Échec envoi OTP: {result.get('message', 'Unknown error')}")
            except Exception as e:
                print(f"❌ Erreur lors de l'envoi OTP: {str(e)}")

        # Lancer l'envoi en arrière-plan
        thread = threading.Thread(target=send_otp_async)
        thread.start()

        # Réponse différente selon DEBUG mode
        response_data = {
            'success': True,
            'message': 'Code OTP généré avec succès',
            'phone_number': phone_number,
            'expires_at': otp.expires_at.isoformat(),
        }

        # En mode DEBUG, retourner le code OTP pour faciliter les tests
        from django.conf import settings
        if settings.DEBUG:
            response_data['otp_code'] = otp_code
            response_data['debug'] = True

        return Response(response_data, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class VerifyOTPView(APIView):
    """
    EXISTING ENDPOINT: POST /api/auth/verify-otp/
    DO NOT MODIFY - Already integrated in production
    """

    @extend_schema(
        tags=['Authentication'],
        summary='Vérifier un code OTP',
        description='Vérifie la validité d\'un code OTP',
        request={
            'type': 'object',
            'properties': {
                'phone_number': {'type': 'string', 'example': '+237690000000'},
                'otp_code': {'type': 'string', 'example': '123456'},
                'user_type': {'type': 'string', 'enum': ['driver', 'customer']},
            },
            'required': ['phone_number', 'otp_code', 'user_type']
        },
        responses={
            200: {'description': 'OTP vérifié avec succès'},
            400: {'description': 'Code OTP invalide ou expiré'},
        }
    )
    def post(self, request):
        """
        Vérifier un code OTP
        """
        from .serializers import VerifyOTPSerializer

        serializer = VerifyOTPSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Données invalides',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data['phone_number']
        otp_code = serializer.validated_data['otp_code']
        user_type = serializer.validated_data['user_type']

        print(f"🔍 Verifying OTP for phone: {phone_number}, user_type: {user_type}, code: {otp_code}")

        try:
            # DEBUG: Vérifier tous les OTP pour ce numéro
            all_otps = OTPVerification.objects.filter(phone_number=phone_number)
            print(f"📊 Total OTPs for {phone_number}: {all_otps.count()}")
            for otp_item in all_otps:
                print(f"   - Code: {otp_item.otp_code}, UserType: {otp_item.user_type}, Verified: {otp_item.is_verified}, Expired: {otp_item.is_expired()}, Created: {otp_item.created_at}")

            # Récupérer l'OTP le plus récent non vérifié
            otp = OTPVerification.objects.filter(
                phone_number=phone_number,
                user_type=user_type,
                is_verified=False
            ).order_by('-created_at').first()

            if not otp:
                print(f"❌ No valid OTP found for phone: {phone_number}, user_type: {user_type}")
                return Response({
                    'success': False,
                    'error': 'Aucun code OTP trouvé pour ce numéro'
                }, status=status.HTTP_404_NOT_FOUND)

            # Vérifier si le code est expiré
            if otp.is_expired():
                return Response({
                    'success': False,
                    'error': 'Le code OTP a expiré. Veuillez demander un nouveau code.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Vérifier le nombre de tentatives
            if not otp.can_attempt():
                return Response({
                    'success': False,
                    'error': 'Nombre maximum de tentatives atteint. Veuillez demander un nouveau code.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Incrémenter les tentatives
            otp.attempts += 1
            otp.save()

            # Vérifier le code
            if otp.otp_code != otp_code:
                remaining = 3 - otp.attempts
                return Response({
                    'success': False,
                    'error': f'Code OTP incorrect. Il vous reste {remaining} tentative(s).',
                    'attempts_remaining': remaining
                }, status=status.HTTP_400_BAD_REQUEST)

            # Code correct - marquer comme vérifié
            otp.is_verified = True
            otp.save()

            return Response({
                'success': True,
                'message': 'Code OTP vérifié avec succès',
                'phone_number': phone_number,
                'user_type': user_type
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'success': False,
                'error': f'Erreur lors de la vérification: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)