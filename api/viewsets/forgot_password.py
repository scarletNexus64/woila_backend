from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from ..serializers import ForgotPasswordSerializer
from ..models import UserDriver, UserCustomer
import logging

logger = logging.getLogger('api')


class ForgotPasswordView(APIView):
    """
    API pour réinitialiser le mot de passe d'un utilisateur
    """
    
    @extend_schema(
        tags=['Authentication'],
        summary='Réinitialiser le mot de passe',
        description='Permet de changer le mot de passe d\'un utilisateur en fournissant son numéro de téléphone et le nouveau mot de passe',
        request=ForgotPasswordSerializer,
        responses={
            200: {
                'description': 'Mot de passe mis à jour avec succès',
                'examples': {
                    'application/json': {
                        'success': True,
                        'message': 'Mot de passe mis à jour avec succès'
                    }
                }
            },
            400: {'description': 'Données invalides'},
            404: {'description': 'Utilisateur introuvable'}
        }
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            new_password = serializer.validated_data['new_password']
            
            try:
                # Mettre à jour le mot de passe
                user.set_password(new_password)
                user.save()
                
                logger.info(f"Mot de passe réinitialisé pour {user.phone_number} ({serializer.validated_data['user_type']})")
                
                return Response({
                    'success': True,
                    'message': 'Mot de passe mis à jour avec succès'
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                logger.error(f"Erreur lors de la réinitialisation du mot de passe: {str(e)}")
                return Response({
                    'success': False,
                    'message': 'Une erreur est survenue lors de la mise à jour du mot de passe'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': False,
            'message': 'Données invalides',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)