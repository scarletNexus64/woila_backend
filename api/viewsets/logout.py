from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema, OpenApiExample
from ..serializers import LogoutSerializer
from ..models import Token


@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(APIView):
    """
    Vue pour la déconnexion des utilisateurs
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
            ),
            OpenApiExample(
                'Invalid Token',
                summary='Token invalide',
                description='Erreur lors de la déconnexion avec un token invalide',
                value={
                    'success': False,
                    'message': 'Token invalide ou déjà expiré'
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