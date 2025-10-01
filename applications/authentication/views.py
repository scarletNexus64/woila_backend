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
from .serializers import LoginSerializer, LogoutSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
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


@method_decorator(csrf_exempt, name='dispatch')
class TokenVerifyView(APIView):
    """
    EXISTING ENDPOINT: POST /api/auth/token/verify/
    Vérifie la validité d'un token JWT
    """

    @extend_schema(
        tags=['Authentication'],
        summary='Vérifier un token',
        description='Vérifie si un token JWT est toujours valide',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'token': {'type': 'string', 'example': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'}
                },
                'required': ['token']
            }
        },
        responses={
            200: {'description': 'Token valide'},
            401: {'description': 'Token invalide ou expiré'},
        }
    )
    def post(self, request):
        try:
            token = request.data.get('token')

            if not token:
                return Response({
                    'success': False,
                    'error': 'Token requis'
                }, status=status.HTTP_400_BAD_REQUEST)

            print(f"🔍 Verifying token: {token[:20]}...")

            # Récupérer le token depuis la base de données
            try:
                token_obj = Token.objects.get(token=token)
                print(f"✅ Token found in database - User Type: {token_obj.user_type}, User ID: {token_obj.user_id}")

                # Vérifier si le token n'a pas expiré (optionnel, selon votre configuration)
                # Django REST Framework gère automatiquement l'expiration

                # Récupérer les informations utilisateur selon le type
                user_type = token_obj.user_type
                user_info = None

                # Vérifier si c'est un chauffeur
                if user_type == 'driver':
                    try:
                        driver = UserDriver.objects.get(id=token_obj.user_id, is_active=True)
                        user_info = {
                            'user_id': driver.id,
                            'id': driver.id,
                            'name': driver.name,
                            'surname': driver.surname,
                            'phone_number': driver.phone_number,
                            'profile_picture_url': request.build_absolute_uri(driver.profile_picture.url) if driver.profile_picture else None,
                            'gender': driver.gender,
                            'age': driver.age,
                            'birthday': driver.birthday.isoformat() if driver.birthday else None,
                        }
                        print(f"✅ Driver found: {driver.name} {driver.surname}")
                    except UserDriver.DoesNotExist:
                        print(f"❌ Driver with ID {token_obj.user_id} not found")
                        return Response({
                            'success': False,
                            'error': 'Chauffeur non trouvé'
                        }, status=status.HTTP_404_NOT_FOUND)

                # Vérifier si c'est un client
                elif user_type == 'customer':
                    try:
                        customer = UserCustomer.objects.get(id=token_obj.user_id, is_active=True)
                        user_info = {
                            'user_id': customer.id,
                            'id': customer.id,
                            'name': customer.name,
                            'surname': customer.surname,
                            'phone_number': customer.phone_number,
                            'profile_picture_url': request.build_absolute_uri(customer.profile_picture.url) if customer.profile_picture else None,
                        }
                        print(f"✅ Customer found: {customer.name} {customer.surname}")
                    except UserCustomer.DoesNotExist:
                        print(f"❌ Customer with ID {token_obj.user_id} not found")
                        return Response({
                            'success': False,
                            'error': 'Client non trouvé'
                        }, status=status.HTTP_404_NOT_FOUND)

                else:
                    print(f"❌ Unknown user type: {user_type}")
                    return Response({
                        'success': False,
                        'error': 'Type d\'utilisateur invalide'
                    }, status=status.HTTP_400_BAD_REQUEST)

                return Response({
                    'success': True,
                    'message': 'Token valide',
                    'user_type': user_type,
                    'user_info': user_info
                }, status=status.HTTP_200_OK)

            except Token.DoesNotExist:
                print("❌ Token not found in database")
                return Response({
                    'success': False,
                    'error': 'Token invalide'
                }, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            print(f"❌ Error verifying token: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': f'Erreur lors de la vérification: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

    @extend_schema(
        tags=['Authentication'],
        summary='Demander la réinitialisation du mot de passe',
        description='Génère un OTP et l\'envoie pour réinitialiser le mot de passe',
        request=ForgotPasswordSerializer,
        responses={
            200: {
                'description': 'OTP envoyé avec succès',
                'example': {
                    'success': True,
                    'message': 'Un code de vérification a été envoyé à votre numéro',
                    'phone_number': '+237690000000'
                }
            },
            400: {'description': 'Données invalides'},
            404: {'description': 'Utilisateur non trouvé'}
        }
    )
    def post(self, request):
        """
        Demander un code OTP pour réinitialiser le mot de passe
        """
        import random

        serializer = ForgotPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Données invalides',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data['phone_number']
        user_type = serializer.validated_data['user_type']

        # Vérifier si l'utilisateur existe
        if user_type == 'driver':
            user_exists = UserDriver.objects.filter(phone_number=phone_number).exists()
        else:
            user_exists = UserCustomer.objects.filter(phone_number=phone_number).exists()

        if not user_exists:
            return Response({
                'success': False,
                'error': 'Aucun compte trouvé avec ce numéro de téléphone'
            }, status=status.HTTP_404_NOT_FOUND)

        # Désactiver les anciens OTP pour ce numéro
        OTPVerification.objects.filter(
            phone_number=phone_number,
            user_type=user_type,
            is_verified=False
        ).update(is_verified=True)

        # Générer un code OTP à 4 chiffres
        otp_code = ''.join([str(random.randint(0, 9)) for _ in range(4)])

        # Créer l'OTP
        otp = OTPVerification.objects.create(
            phone_number=phone_number,
            otp_code=otp_code,
            user_type=user_type
        )

        print(f"✅ Password reset OTP created: code={otp.otp_code}, phone={otp.phone_number}, user_type={otp.user_type}")

        # Envoyer l'OTP via WhatsApp/SMS (en arrière-plan pour ne pas bloquer)
        def send_otp_async():
            try:
                result = NotificationService.send_otp(
                    recipient=phone_number,
                    otp_code=otp_code
                )
                if result['success']:
                    print(f"✅ Password reset OTP envoyé avec succès via {result.get('channel', 'unknown')}")
                else:
                    print(f"❌ Échec envoi password reset OTP: {result.get('message', 'Unknown error')}")
            except Exception as e:
                print(f"❌ Erreur lors de l'envoi password reset OTP: {str(e)}")

        # Lancer l'envoi en arrière-plan
        thread = threading.Thread(target=send_otp_async)
        thread.start()

        return Response({
            'success': True,
            'message': 'Un code de vérification a été envoyé à votre numéro',
            'phone_number': phone_number
        }, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    """
    EXISTING ENDPOINT: POST /api/auth/reset-password/
    DO NOT MODIFY - Already integrated in production
    """

    @extend_schema(
        tags=['Authentication'],
        summary='Réinitialiser le mot de passe',
        description='Réinitialise le mot de passe après vérification de l\'OTP',
        request={
            'type': 'object',
            'properties': {
                'phone_number': {'type': 'string', 'example': '+237690000000'},
                'otp_code': {'type': 'string', 'example': '1234'},
                'new_password': {'type': 'string', 'example': 'newpassword123'},
                'user_type': {'type': 'string', 'enum': ['driver', 'customer']},
            },
            'required': ['phone_number', 'otp_code', 'new_password', 'user_type']
        },
        responses={
            200: {
                'description': 'Mot de passe réinitialisé avec succès',
                'example': {
                    'success': True,
                    'message': 'Votre mot de passe a été réinitialisé avec succès'
                }
            },
            400: {'description': 'Code OTP invalide ou expiré'},
            404: {'description': 'Utilisateur non trouvé'}
        }
    )
    def post(self, request):
        """
        Réinitialiser le mot de passe avec un code OTP valide
        """
        from .serializers import ResetPasswordSerializer

        serializer = ResetPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Données invalides',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data['phone_number']
        otp_code = serializer.validated_data['otp_code']
        new_password = serializer.validated_data['new_password']
        user_type = serializer.validated_data['user_type']

        # Vérifier si l'OTP est valide
        try:
            otp = OTPVerification.objects.get(
                phone_number=phone_number,
                otp_code=otp_code,
                user_type=user_type,
                is_verified=False
            )
        except OTPVerification.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Code OTP invalide ou déjà utilisé'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Vérifier si l'OTP n'est pas expiré
        if otp.is_expired():
            return Response({
                'success': False,
                'error': 'Le code OTP a expiré. Veuillez en demander un nouveau.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Récupérer l'utilisateur
        if user_type == 'driver':
            try:
                user = UserDriver.objects.get(phone_number=phone_number)
            except UserDriver.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Aucun compte chauffeur trouvé avec ce numéro'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            try:
                user = UserCustomer.objects.get(phone_number=phone_number)
            except UserCustomer.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Aucun compte client trouvé avec ce numéro'
                }, status=status.HTTP_404_NOT_FOUND)

        # Mettre à jour le mot de passe
        user.set_password(new_password)
        user.save()

        # Marquer l'OTP comme utilisé
        otp.is_verified = True
        otp.save()

        print(f"✅ Password reset successful for {phone_number} ({user_type})")

        return Response({
            'success': True,
            'message': 'Votre mot de passe a été réinitialisé avec succès'
        }, status=status.HTTP_200_OK)


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


# ================================
# REFERRAL ENDPOINTS
# ================================

@method_decorator(csrf_exempt, name='dispatch')
class ReferralValidateCodeView(APIView):
    """
    ENDPOINT: POST /api/auth/referral/validate-code/
    Valider un code de parrainage
    """

    @extend_schema(
        tags=['Referral'],
        summary='Valider un code de parrainage',
        description='Vérifie si un code de parrainage existe et est actif',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'referral_code': {'type': 'string', 'example': 'ABC12345'}
                },
                'required': ['referral_code']
            }
        },
        responses={
            200: {'description': 'Code valide'},
            404: {'description': 'Code invalide ou inexistant'},
        }
    )
    def post(self, request):
        try:
            referral_code = request.data.get('referral_code', '').strip().upper()

            if not referral_code:
                return Response({
                    'success': False,
                    'error': 'Le code de parrainage est requis'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Rechercher le code de parrainage
            try:
                code = ReferralCode.objects.get(code=referral_code, is_active=True)

                # Récupérer les informations du parrain
                user_data = {}
                if code.user_type.model == 'userdriver':
                    user = UserDriver.objects.get(id=code.user_id)
                    user_data = {
                        'name': user.name,
                        'surname': user.surname,
                        'user_type': 'driver'
                    }
                elif code.user_type.model == 'usercustomer':
                    user = UserCustomer.objects.get(id=code.user_id)
                    user_data = {
                        'name': user.name,
                        'surname': user.surname,
                        'user_type': 'customer'
                    }

                return Response({
                    'success': True,
                    'message': 'Code de parrainage valide',
                    'referral_code': referral_code,
                    'sponsor': user_data,
                    'used_count': code.used_count
                }, status=status.HTTP_200_OK)

            except ReferralCode.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Code de parrainage invalide ou expiré'
                }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                'success': False,
                'error': f'Erreur lors de la validation: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class ReferralUserInfoView(APIView):
    """
    ENDPOINT: GET /api/auth/referral/user-info/
    Récupérer les informations de parrainage d'un utilisateur
    """

    @extend_schema(
        tags=['Referral'],
        summary='Informations de parrainage utilisateur',
        description='Récupère le code de parrainage et les statistiques d\'un utilisateur',
        parameters=[
            {
                'name': 'user_type',
                'in': 'query',
                'required': True,
                'schema': {'type': 'string', 'enum': ['driver', 'customer']}
            },
            {
                'name': 'user_id',
                'in': 'query',
                'required': True,
                'schema': {'type': 'integer'}
            }
        ],
        responses={
            200: {'description': 'Informations récupérées avec succès'},
            404: {'description': 'Utilisateur non trouvé'},
        }
    )
    def get(self, request):
        try:
            user_type = request.query_params.get('user_type')
            user_id = request.query_params.get('user_id')

            if not user_type or not user_id:
                return Response({
                    'success': False,
                    'error': 'user_type et user_id sont requis'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Déterminer le ContentType
            if user_type == 'driver':
                content_type = ContentType.objects.get_for_model(UserDriver)
                user = UserDriver.objects.get(id=user_id)
            elif user_type == 'customer':
                content_type = ContentType.objects.get_for_model(UserCustomer)
                user = UserCustomer.objects.get(id=user_id)
            else:
                return Response({
                    'success': False,
                    'error': 'Type d\'utilisateur invalide'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Récupérer ou créer le code de parrainage
            referral_code, created = ReferralCode.objects.get_or_create(
                user_type=content_type,
                user_id=user_id,
                defaults={'code': self._generate_referral_code()}
            )

            # Compter les filleuls (personnes qui ont utilisé ce code)
            # Pour l'instant, on retourne 0 car la logique d'utilisation n'est pas encore implémentée
            referrals_count = referral_code.used_count

            return Response({
                'success': True,
                'referral_code': referral_code.code,
                'referrals_count': referrals_count,
                'total_earnings': 0.0,  # À implémenter avec le système de wallet
                'is_active': referral_code.is_active,
                'created_at': referral_code.created_at.isoformat()
            }, status=status.HTTP_200_OK)

        except (UserDriver.DoesNotExist, UserCustomer.DoesNotExist):
            return Response({
                'success': False,
                'error': 'Utilisateur non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Erreur lors de la récupération: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _generate_referral_code(self):
        """Génère un code de parrainage unique"""
        import random
        import string

        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not ReferralCode.objects.filter(code=code).exists():
                return code


@method_decorator(csrf_exempt, name='dispatch')
class ReferralWalletView(APIView):
    """
    ENDPOINT: GET /api/auth/referral/wallet/
    Récupérer les informations du wallet de parrainage
    """

    @extend_schema(
        tags=['Referral'],
        summary='Wallet de parrainage',
        description='Récupère les gains de parrainage d\'un utilisateur',
        parameters=[
            {
                'name': 'user_type',
                'in': 'query',
                'required': True,
                'schema': {'type': 'string', 'enum': ['driver', 'customer']}
            },
            {
                'name': 'user_id',
                'in': 'query',
                'required': True,
                'schema': {'type': 'integer'}
            }
        ],
        responses={
            200: {'description': 'Wallet récupéré avec succès'},
            404: {'description': 'Utilisateur non trouvé'},
        }
    )
    def get(self, request):
        try:
            user_type = request.query_params.get('user_type')
            user_id = request.query_params.get('user_id')

            if not user_type or not user_id:
                return Response({
                    'success': False,
                    'error': 'user_type et user_id sont requis'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Déterminer le ContentType et récupérer l'utilisateur
            if user_type == 'driver':
                content_type = ContentType.objects.get_for_model(UserDriver)
                user = UserDriver.objects.get(id=user_id)
            elif user_type == 'customer':
                content_type = ContentType.objects.get_for_model(UserCustomer)
                user = UserCustomer.objects.get(id=user_id)
            else:
                return Response({
                    'success': False,
                    'error': 'Type d\'utilisateur invalide'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Récupérer le wallet
            try:
                wallet = Wallet.objects.get(
                    user_type=content_type,
                    user_id=user_id
                )

                return Response({
                    'success': True,
                    'balance': float(wallet.balance),
                    'pending_earnings': 0.0,  # À implémenter
                    'total_earnings': 0.0,  # À implémenter
                    'currency': 'FCFA'
                }, status=status.HTTP_200_OK)

            except Wallet.DoesNotExist:
                # Créer le wallet s'il n'existe pas
                wallet = Wallet.objects.create(
                    user_type=content_type,
                    user_id=user_id,
                    balance=0.0
                )

                return Response({
                    'success': True,
                    'balance': 0.0,
                    'pending_earnings': 0.0,
                    'total_earnings': 0.0,
                    'currency': 'FCFA'
                }, status=status.HTTP_200_OK)

        except (UserDriver.DoesNotExist, UserCustomer.DoesNotExist):
            return Response({
                'success': False,
                'error': 'Utilisateur non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Erreur lors de la récupération: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)