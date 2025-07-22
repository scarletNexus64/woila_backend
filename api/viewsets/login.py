from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema, OpenApiExample
from ..serializers import LoginSerializer
from ..models import Token, UserDriver, UserCustomer


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    """
    Vue pour la connexion des utilisateurs (chauffeurs et clients)
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
                    'name': user.name,
                    'surname': user.surname,
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