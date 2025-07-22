from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema, OpenApiExample
from ..serializers import RegisterDriverSerializer, RegisterCustomerSerializer
from ..models import Token


@method_decorator(csrf_exempt, name='dispatch')
class RegisterDriverView(APIView):
    """
    Vue pour l'inscription des chauffeurs
    """
    
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
                    'birthday': '1988-05-15'
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
                    'token': '550e8400-e29b-41d4-a716-446655440000',
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
            # Créer le chauffeur
            driver = serializer.save()
            
            # Créer un token d'authentification
            token = Token.objects.create(
                user_type='driver',
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
                'birthday': driver.birthday.isoformat() if driver.birthday else None
            }
            
            return Response({
                'success': True,
                'message': 'Inscription chauffeur réussie',
                'token': str(token.token),
                'user_type': 'driver',
                'user_id': driver.id,
                'user_info': user_info
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class RegisterCustomerView(APIView):
    """
    Vue pour l'inscription des clients
    """
    
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
                    'surname': 'Martin'
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
                    'token': '550e8400-e29b-41d4-a716-446655440001',
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
            # Créer le client
            customer = serializer.save()
            
            # Créer un token d'authentification
            token = Token.objects.create(
                user_type='customer',
                user_id=customer.id
            )
            
            # Préparer les informations du client
            user_info = {
                'id': customer.id,
                'name': customer.name,
                'surname': customer.surname,
                'phone_number': customer.phone_number
            }
            
            return Response({
                'success': True,
                'message': 'Inscription client réussie',
                'token': str(token.token),
                'user_type': 'customer',
                'user_id': customer.id,
                'user_info': user_info
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)