"""
ViewSet pour gérer les tokens FCM et déclencher les notifications en attente
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.contenttypes.models import ContentType
from drf_spectacular.utils import extend_schema

from ..models import FCMToken, Token, UserDriver, UserCustomer, Notification
from ..services.notification_service import NotificationService
from ..serializers import FCMTokenSerializer

import logging
logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class FCMTokenCreateView(APIView):
    """
    Vue pour enregistrer un token FCM et déclencher les notifications en attente
    """
    
    @extend_schema(
        tags=['FCM'],
        summary='Enregistrer un token FCM',
        description='Enregistre un token FCM et envoie les notifications en attente comme la notification de bienvenue',
        request=FCMTokenSerializer,
        responses={
            201: {'description': 'Token FCM enregistré avec succès'},
            400: {'description': 'Données invalides'},
        }
    )
    def post(self, request):
        """
        Enregistrer un nouveau token FCM
        """
        serializer = FCMTokenSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                # Récupérer l'utilisateur depuis le token d'authentification
                auth_token = request.headers.get('Authorization', '').replace('Bearer ', '')
                token_obj = Token.objects.filter(token=auth_token, is_active=True).first()
                
                if not token_obj:
                    return Response({
                        'success': False,
                        'message': 'Token d\'authentification invalide'
                    }, status=status.HTTP_401_UNAUTHORIZED)
                
                # Récupérer l'utilisateur
                if token_obj.user_type == 'driver':
                    user = UserDriver.objects.get(id=token_obj.user_id)
                else:
                    user = UserCustomer.objects.get(id=token_obj.user_id)
                
                # Créer ou mettre à jour le token FCM
                fcm_token_obj = serializer.save(user=user)
                
                user_display = f"{user.name} {user.surname}" if hasattr(user, 'name') else f"Client {user.phone_number}"
                logger.info(f"📱 Token FCM enregistré pour {user_display}")
                
                # Vérifier s'il y a une notification de bienvenue en attente
                content_type = ContentType.objects.get_for_model(user)
                
                # Vérifier si l'utilisateur n'a jamais reçu de notification de bienvenue FCM
                welcome_notification = Notification.objects.filter(
                    user_type=content_type,
                    user_id=user.id,
                    notification_type='welcome',
                    is_read=False  # Non lue = probablement pas reçue en push
                ).first()
                
                # Si c'est un nouvel utilisateur (moins de 5 minutes depuis la création)
                from django.utils import timezone
                from datetime import timedelta
                
                is_new_user = hasattr(user, 'created_at') and (
                    timezone.now() - user.created_at < timedelta(minutes=5)
                )
                
                if is_new_user and not welcome_notification:
                    # Envoyer la notification de bienvenue maintenant qu'on a le token FCM
                    try:
                        success = NotificationService.send_welcome_notification(user)
                        if success:
                            logger.info(f"🎉 Notification de bienvenue envoyée à {user.name} après enregistrement FCM")
                    except Exception as e:
                        logger.error(f"Erreur envoi notification bienvenue: {e}")
                
                return Response({
                    'success': True,
                    'message': 'Token FCM enregistré avec succès',
                    'fcm_token_id': fcm_token_obj.id,
                    'welcome_notification_sent': is_new_user and not welcome_notification
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"Erreur lors de l'enregistrement du token FCM: {str(e)}")
                return Response({
                    'success': False,
                    'message': f'Erreur: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)