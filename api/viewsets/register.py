from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema, OpenApiExample
from ..serializers import RegisterDriverSerializer, RegisterCustomerSerializer
from ..models import Token, ReferralCode, Wallet, GeneralConfig
from django.db import transaction
from django.contrib.contenttypes.models import ContentType



@method_decorator(csrf_exempt, name='dispatch')
class RegisterDriverView(APIView):
    """
    Vue pour l'inscription des chauffeurs
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

                    # Le bonus de parrainage est géré automatiquement dans le serializer
                    # Pas besoin de logique supplémentaire ici
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
    Vue pour l'inscription des clients
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
                    'name': 'Marie',
                    'surname': 'Martin',
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
                        'name': 'Marie',
                        'surname': 'Martin',
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

                    # Le bonus de parrainage est géré automatiquement dans le serializer
                    # Pas besoin de logique supplémentaire ici

                    # Préparer les informations du client
                    user_info = {
                        'id': customer.id,
                        'name': customer.name,
                        'surname': customer.surname,
                        'phone_number': customer.phone_number,
                        'profile_picture_url': customer.get_profile_picture_url(request) if customer.profile_picture else None
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