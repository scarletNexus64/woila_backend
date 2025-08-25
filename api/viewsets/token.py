from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema, OpenApiExample
from ..models import Token, UserDriver, UserCustomer
from rest_framework import serializers


class TokenVerifySerializer(serializers.Serializer):
    """
    Serializer pour la vérification de token
    """
    token = serializers.UUIDField()


@method_decorator(csrf_exempt, name='dispatch')
class TokenVerifyView(APIView):
    """
    Vue pour vérifier la validité d'un token
    """
    
    @extend_schema(
        tags=['Token Management'],
        summary='Vérifier un token',
        description='Vérifier si un token d\'authentification est valide et récupérer les informations utilisateur associées',
        request=TokenVerifySerializer,
        responses={
            200: {'description': 'Token valide'},
            401: {'description': 'Token invalide ou expiré'},
            400: {'description': 'Données invalides'},
        },
        examples=[
            OpenApiExample(
                'Token Verification',
                summary='Vérification de token',
                description='Vérifier la validité d\'un token',
                value={
                    'token': '550e8400-e29b-41d4-a716-446655440000'
                },
                request_only=True,
            ),
            OpenApiExample(
                'Valid Token Response',
                summary='Token valide',
                description='Réponse pour un token valide avec informations utilisateur',
                value={
                    'success': True,
                    'message': 'Token valide',
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
                    },
                    'token_created_at': '2023-12-01T10:30:00Z'
                },
                response_only=True,
            ),
            OpenApiExample(
                'Invalid Token Response',
                summary='Token invalide',
                description='Réponse pour un token invalide ou expiré',
                value={
                    'success': False,
                    'message': 'Token invalide ou expiré'
                },
                response_only=True,
            )
        ]
    )
    def post(self, request):
        """
        Vérifier la validité d'un token et récupérer les informations utilisateur
        """
        serializer = TokenVerifySerializer(data=request.data)
        
        if serializer.is_valid():
            token_value = serializer.validated_data['token']
            
            try:
                # Rechercher le token actif
                token = Token.objects.get(
                    token=token_value,
                    is_active=True
                )
                
                # Récupérer les informations utilisateur
                if token.user_type == 'driver':
                    try:
                        user = UserDriver.objects.get(id=token.user_id, is_active=True)
                        user_info = {
                            'id': user.id,
                            'name': user.name,
                            'surname': user.surname,
                            'phone_number': user.phone_number,
                            'gender': user.gender,
                            'age': user.age,
                            'birthday': user.birthday.isoformat() if user.birthday else None
                        }
                    except UserDriver.DoesNotExist:
                        return Response({
                            'success': False,
                            'message': 'Utilisateur associé au token introuvable ou inactif'
                        }, status=status.HTTP_401_UNAUTHORIZED)
                        
                else:  # customer
                    try:
                        user = UserCustomer.objects.get(id=token.user_id, is_active=True)
                        user_info = {
                            'id': user.id,
                            'phone_number': user.phone_number
                        }
                    except UserCustomer.DoesNotExist:
                        return Response({
                            'success': False,
                            'message': 'Utilisateur associé au token introuvable ou inactif'
                        }, status=status.HTTP_401_UNAUTHORIZED)
                
                return Response({
                    'success': True,
                    'message': 'Token valide',
                    'user_type': token.user_type,
                    'user_id': token.user_id,
                    'user_info': user_info,
                    'token_created_at': token.created_at.isoformat()
                }, status=status.HTTP_200_OK)
                
            except Token.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Token invalide ou expiré'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class TokenRefreshView(APIView):
    """
    Vue pour rafraîchir un token (optionnel pour le MVP)
    """
    
    @extend_schema(
        tags=['Token Management'],
        summary='Rafraîchir un token',
        description='Rafraîchir un token d\'authentification existant (génère un nouveau token)',
        request=TokenVerifySerializer,
        responses={
            200: {'description': 'Token rafraîchi avec succès'},
            401: {'description': 'Token invalide ou expiré'},
            400: {'description': 'Données invalides'},
        },
        examples=[
            OpenApiExample(
                'Token Refresh',
                summary='Rafraîchissement de token',
                description='Rafraîchir un token existant',
                value={
                    'token': '550e8400-e29b-41d4-a716-446655440000'
                },
                request_only=True,
            ),
            OpenApiExample(
                'Refreshed Token Response',
                summary='Token rafraîchi',
                description='Nouveau token généré',
                value={
                    'success': True,
                    'message': 'Token rafraîchi avec succès',
                    'new_token': '550e8400-e29b-41d4-a716-446655440001',
                    'user_type': 'driver',
                    'user_id': 1
                },
                response_only=True,
            )
        ]
    )
    def post(self, request):
        """
        Rafraîchir un token existant (générer un nouveau token)
        """
        serializer = TokenVerifySerializer(data=request.data)
        
        if serializer.is_valid():
            token_value = serializer.validated_data['token']
            
            try:
                # Rechercher le token actif
                old_token = Token.objects.get(
                    token=token_value,
                    is_active=True
                )
                
                # Vérifier que l'utilisateur existe toujours
                if old_token.user_type == 'driver':
                    UserDriver.objects.get(id=old_token.user_id, is_active=True)
                else:
                    UserCustomer.objects.get(id=old_token.user_id, is_active=True)
                
                # Désactiver l'ancien token
                old_token.is_active = False
                old_token.save()
                
                # Créer un nouveau token
                new_token = Token.objects.create(
                    user_type=old_token.user_type,
                    user_id=old_token.user_id
                )
                
                return Response({
                    'success': True,
                    'message': 'Token rafraîchi avec succès',
                    'new_token': str(new_token.token),
                    'user_type': new_token.user_type,
                    'user_id': new_token.user_id
                }, status=status.HTTP_200_OK)
                
            except Token.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Token invalide ou expiré'
                }, status=status.HTTP_401_UNAUTHORIZED)
                
            except (UserDriver.DoesNotExist, UserCustomer.DoesNotExist):
                return Response({
                    'success': False,
                    'message': 'Utilisateur associé au token introuvable ou inactif'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)