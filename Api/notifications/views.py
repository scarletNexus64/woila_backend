# EXISTING ENDPOINTS - DO NOT MODIFY URLs - Already integrated in production
# Notification views migrated from api.viewsets.notifications and api.viewsets.fcm

import logging
import traceback
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.contrib.contenttypes.models import ContentType

logger = logging.getLogger(__name__)

# Import from api app (legacy)
from users.models import UserDriver, UserCustomer
from .models import Notification, FCMToken
from .serializers import (
    NotificationSerializer, NotificationListSerializer,
    FCMTokenRegisterSerializer, FCMTokenSerializer, FCMTokenListSerializer
)
from notifications.services.notification_service import NotificationService
from notifications.services.fcm_service import FCMService


def get_user_from_token(request):
    """Helper function to get user from authorization token"""
    auth_header = request.META.get('HTTP_AUTHORIZATION')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None, Response({
            'success': False,
            'error': 'Token d\'authentification manquant'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    token_value = auth_header[7:]  # Remove 'Bearer ' prefix
    try:
        from authentication.models import Token
        token = Token.objects.get(token=token_value, is_active=True)
        if token.user_type == 'driver':
            user = UserDriver.objects.get(id=token.user_id)
        else:
            user = UserCustomer.objects.get(id=token.user_id)
        return user, None
    except Token.DoesNotExist:
        return None, Response({
            'success': False,
            'error': 'Token invalide'
        }, status=status.HTTP_401_UNAUTHORIZED)


@method_decorator(csrf_exempt, name='dispatch')
class NotificationListView(APIView):
    """
    EXISTING ENDPOINT: GET /api/notifications/
    DO NOT MODIFY - Already integrated in production
    """
    
    @extend_schema(
        tags=['Notifications'],
        summary='Liste des notifications',
        description='Récupère toutes les notifications de l\'utilisateur connecté',
        parameters=[
            OpenApiParameter(
                name='include_read',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Inclure les notifications lues (défaut: true)',
                default=True
            ),
            OpenApiParameter(
                name='limit',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Nombre maximum de notifications à retourner',
                default=50
            )
        ],
        responses={
            200: NotificationListSerializer(many=True),
            401: {'description': 'Non autorisé'},
        },
        examples=[
            OpenApiExample(
                'Successful Response',
                summary='Réponse réussie',
                description='Liste des notifications de l\'utilisateur',
                value={
                    'success': True,
                    'count': 5,
                    'unread_count': 2,
                    'notifications': [
                        {
                            'id': 1,
                            'title': '🎉 Bienvenue sur WOILA !',
                            'content': 'Bonjour Jean, Bienvenue dans la famille WOILA !...',
                            'notification_type': 'welcome',
                            'type_display': 'Notification de bienvenue',
                            'is_read': False,
                            'created_at': '2024-01-15T10:30:00Z',
                            'time_ago': 'Il y a 2 heures'
                        }
                    ]
                },
                response_only=True,
            )
        ]
    )
    def get(self, request):
        """
        Récupère les notifications de l'utilisateur connecté
        """
        try:
            # Obtenir les paramètres de requête
            include_read = request.query_params.get('include_read', 'true').lower() == 'true'
            limit = int(request.query_params.get('limit', 50))
            
            # Obtenir l'utilisateur depuis le token
            user, auth_error = get_user_from_token(request)
            if auth_error:
                return auth_error
            
            # Récupérer les notifications
            notifications = NotificationService.get_user_notifications(
                user=user,
                include_read=include_read,
                include_deleted=False
            )[:limit]
            
            # Compter les notifications non lues
            unread_count = NotificationService.get_unread_count(user)
            
            # Sérialiser les données
            serializer = NotificationListSerializer(notifications, many=True)
            
            return Response({
                'success': True,
                'count': len(notifications),
                'unread_count': unread_count,
                'notifications': serializer.data
            }, status=status.HTTP_200_OK)
            
        except (UserDriver.DoesNotExist, UserCustomer.DoesNotExist):
            return Response({
                'success': False,
                'error': 'Utilisateur introuvable'
            }, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({
                'success': False,
                'error': 'Paramètre limit invalide'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class NotificationUnreadView(APIView):
    """
    EXISTING ENDPOINT: GET /api/notifications/unread/
    DO NOT MODIFY - Already integrated in production
    """
    
    @extend_schema(
        tags=['Notifications'],
        summary='Notifications non lues',
        description='Récupère uniquement les notifications non lues de l\'utilisateur',
        responses={200: NotificationListSerializer(many=True)}
    )
    def get(self, request):
        """
        Récupère uniquement les notifications non lues
        """
        try:
            user, auth_error = get_user_from_token(request)
            if auth_error:
                return auth_error
            
            notifications = NotificationService.get_user_notifications(
                user=user,
                include_read=False,
                include_deleted=False
            )
            
            serializer = NotificationListSerializer(notifications, many=True)
            
            return Response({
                'success': True,
                'count': len(notifications),
                'notifications': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class NotificationDetailView(APIView):
    """
    EXISTING ENDPOINT: GET /api/notifications/{notification_id}/
    DO NOT MODIFY - Already integrated in production
    """
    
    @extend_schema(
        tags=['Notifications'],
        summary='Détail d\'une notification',
        description='Récupère les détails d\'une notification spécifique',
        responses={200: NotificationSerializer}
    )
    def get(self, request, notification_id):
        """
        Récupère une notification spécifique
        """
        try:
            user, auth_error = get_user_from_token(request)
            if auth_error:
                return auth_error
            
            content_type = ContentType.objects.get_for_model(user)
            notification = Notification.objects.get(
                id=notification_id,
                user_type=content_type,
                user_id=user.id,
                is_deleted=False
            )
            
            serializer = NotificationSerializer(notification)
            return Response({
                'success': True,
                'notification': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Notification.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Notification introuvable'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @extend_schema(
        tags=['Notifications'],
        summary='Marquer comme lu',
        description='Marque une notification comme lue',
        responses={200: {'description': 'Notification marquée comme lue'}}
    )
    def patch(self, request, notification_id):
        """
        Marque une notification comme lue
        """
        try:
            user, auth_error = get_user_from_token(request)
            if auth_error:
                return auth_error
            
            success = NotificationService.mark_notification_as_read(notification_id, user)
            
            if success:
                return Response({
                    'success': True,
                    'message': 'Notification marquée comme lue'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': 'Impossible de marquer la notification comme lue'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @extend_schema(
        tags=['Notifications'],
        summary='Supprimer une notification',
        description='Supprime définitivement une notification',
        responses={200: {'description': 'Notification supprimée'}}
    )
    def delete(self, request, notification_id):
        """
        Supprime une notification (soft delete)
        """
        try:
            user, auth_error = get_user_from_token(request)
            if auth_error:
                return auth_error
            
            success = NotificationService.delete_notification(notification_id, user)
            
            if success:
                return Response({
                    'success': True,
                    'message': 'Notification supprimée'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': 'Impossible de supprimer la notification'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class NotificationMarkAllReadView(APIView):
    """
    EXISTING ENDPOINT: POST /api/notifications/mark-all-read/
    DO NOT MODIFY - Already integrated in production
    """
    
    @extend_schema(
        tags=['Notifications'],
        summary='Marquer tout comme lu',
        description='Marque toutes les notifications de l\'utilisateur comme lues',
        responses={200: {'description': 'Toutes les notifications marquées comme lues'}}
    )
    def post(self, request):
        """
        Marque toutes les notifications comme lues
        """
        try:
            user, auth_error = get_user_from_token(request)
            if auth_error:
                return auth_error
            
            # Récupérer toutes les notifications non lues
            content_type = ContentType.objects.get_for_model(user)
            unread_notifications = Notification.objects.filter(
                user_type=content_type,
                user_id=user.id,
                is_read=False,
                is_deleted=False
            )
            
            # Marquer comme lues
            updated_count = 0
            for notification in unread_notifications:
                notification.mark_as_read()
                updated_count += 1
            
            return Response({
                'success': True,
                'message': f'{updated_count} notification(s) marquée(s) comme lue(s)',
                'updated_count': updated_count
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class NotificationStatsView(APIView):
    """
    EXISTING ENDPOINT: GET /api/notifications/stats/
    DO NOT MODIFY - Already integrated in production
    """
    
    @extend_schema(
        tags=['Notifications'],
        summary='Statistiques notifications',
        description='Obtient les statistiques des notifications de l\'utilisateur',
        responses={
            200: {
                'description': 'Statistiques des notifications',
                'example': {
                    'success': True,
                    'stats': {
                        'total': 15,
                        'unread': 3,
                        'today': 2,
                        'this_week': 7,
                        'by_type': {
                            'welcome': 1,
                            'referral_used': 2,
                            'vehicle_approved': 1,
                            'system': 11
                        }
                    }
                }
            }
        }
    )
    def get(self, request):
        """
        Obtient les statistiques des notifications
        """
        try:
            user, auth_error = get_user_from_token(request)
            if auth_error:
                return auth_error
            
            content_type = ContentType.objects.get_for_model(user)
            
            # Statistiques générales
            total = Notification.objects.filter(
                user_type=content_type,
                user_id=user.id,
                is_deleted=False
            ).count()
            
            unread = NotificationService.get_unread_count(user)
            
            # Statistiques temporelles
            from django.utils import timezone
            from datetime import timedelta
            
            now = timezone.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = now - timedelta(days=7)
            
            today = Notification.objects.filter(
                user_type=content_type,
                user_id=user.id,
                is_deleted=False,
                created_at__gte=today_start
            ).count()
            
            this_week = Notification.objects.filter(
                user_type=content_type,
                user_id=user.id,
                is_deleted=False,
                created_at__gte=week_start
            ).count()
            
            # Statistiques par type
            from django.db.models import Count
            by_type = dict(
                Notification.objects.filter(
                    user_type=content_type,
                    user_id=user.id,
                    is_deleted=False
                ).values('notification_type').annotate(
                    count=Count('notification_type')
                ).values_list('notification_type', 'count')
            )
            
            return Response({
                'success': True,
                'stats': {
                    'total': total,
                    'unread': unread,
                    'today': today,
                    'this_week': this_week,
                    'by_type': by_type
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# FCM VIEWS

@method_decorator(csrf_exempt, name='dispatch')
class FCMTokenRegisterView(APIView):
    """
    EXISTING ENDPOINT: POST /api/fcm/register/
    DO NOT MODIFY - Already integrated in production
    """
    authentication_classes = []  # Utiliser notre système d'auth custom via get_user_from_token
    permission_classes = []

    @extend_schema(
        tags=['FCM'],
        summary='Enregistrer un token FCM',
        description='Enregistre ou met à jour le token FCM d\'un utilisateur pour recevoir des notifications push',
        request=FCMTokenRegisterSerializer,
        responses={
            200: {'description': 'Token enregistré avec succès'},
            400: {'description': 'Données invalides'},
            401: {'description': 'Non autorisé'},
        },
        examples=[
            OpenApiExample(
                'Successful Registration',
                summary='Enregistrement réussi',
                description='Exemple d\'enregistrement de token FCM',
                value={
                    'fcm_token': 'dA1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8s9T0u1V2w3X4y5Z6a7B8c9D0e1F2g3H4i5J6k7L8m9N0o1P2q3R4s5T6u7V8w9X0y1Z2a3B4c5D6e7F8g9H0i1J2k3L4m5N6o7P8q9R0s1T2u3V4w5X6y7Z8a9B0c1D2e3F4g5H6i7J8k9L0m1N2o3P4q5R6s7T8u9V0w1X2y3Z4a5B6c7D8e9F0g1H2i3J4k5L6m7N8o9P0q1R2s3T4u5V6w7X8y9Z0a1B2c3D4e5F6g7H8i9J0',
                    'device_info': {
                        'platform': 'android',
                        'version': '13',
                        'device_id': 'android-1234567890'
                    }
                },
                request_only=True,
            )
        ]
    )
    def post(self, request):
        """
        Enregistre un token FCM pour l'utilisateur connecté
        """
        try:
            user, auth_error = get_user_from_token(request)
            if auth_error:
                return auth_error
            
            serializer = FCMTokenRegisterSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'error': 'Données invalides',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            fcm_token_value = serializer.validated_data.get('token') or serializer.validated_data.get('fcm_token')
            device_info = serializer.validated_data.get('device_info', {})
            
            # Enregistrer le token via le service FCM
            fcm_token = FCMService.register_token(
                user=user,
                token=fcm_token_value,
                device_info=device_info
            )
            
            return Response({
                'success': True,
                'message': 'Token FCM enregistré avec succès',
                'token_id': fcm_token.id,
                'device_count': FCMService.get_user_device_count(user)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"❌ Erreur lors de l'enregistrement du token FCM: {str(e)}")
            logger.error(traceback.format_exc())
            return Response({
                'success': False,
                'error': f'Erreur lors de l\'enregistrement du token: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class FCMTokenUnregisterView(APIView):
    """
    EXISTING ENDPOINT: POST /api/fcm/unregister/
    DO NOT MODIFY - Already integrated in production
    """
    
    @extend_schema(
        tags=['FCM'],
        summary='Supprimer un token FCM',
        description='Supprime un token FCM de l\'utilisateur pour arrêter les notifications push',
        request={'type': 'object', 'properties': {'fcm_token': {'type': 'string'}}},
        responses={
            200: {'description': 'Token supprimé avec succès'},
            400: {'description': 'Données invalides'},
            401: {'description': 'Non autorisé'},
        }
    )
    def delete(self, request):
        """
        Supprime un token FCM
        """
        try:
            user, auth_error = get_user_from_token(request)
            if auth_error:
                return auth_error
            
            fcm_token = request.data.get('fcm_token')
            if not fcm_token:
                return Response({
                    'success': False,
                    'error': 'Token FCM requis'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Supprimer le token via le service FCM
            success = FCMService.unregister_token(user=user, token=fcm_token)
            
            if success:
                return Response({
                    'success': True,
                    'message': 'Token FCM supprimé avec succès',
                    'device_count': FCMService.get_user_device_count(user)
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': 'Token non trouvé'
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class FCMTokenListView(APIView):
    """
    EXISTING ENDPOINT: GET /api/fcm/tokens/
    DO NOT MODIFY - Already integrated in production
    """
    
    @extend_schema(
        tags=['FCM'],
        summary='Liste des tokens FCM',
        description='Récupère tous les tokens FCM de l\'utilisateur connecté',
        responses={200: FCMTokenListSerializer(many=True)},
    )
    def get(self, request):
        """
        Récupère la liste des tokens FCM de l'utilisateur
        """
        try:
            user, auth_error = get_user_from_token(request)
            if auth_error:
                return auth_error
            
            content_type = ContentType.objects.get_for_model(user)
            
            fcm_tokens = FCMToken.objects.filter(
                user_type=content_type,
                user_id=user.id
            )
            
            serializer = FCMTokenListSerializer(fcm_tokens, many=True)
            
            return Response({
                'success': True,
                'count': len(fcm_tokens),
                'active_count': fcm_tokens.filter(is_active=True).count(),
                'tokens': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class FCMTokenDetailView(APIView):
    """
    EXISTING ENDPOINT: GET /api/fcm/tokens/{token_id}/
    DO NOT MODIFY - Already integrated in production
    """
    
    @extend_schema(
        tags=['FCM'],
        summary='Détails d\'un token FCM',
        description='Récupère les détails d\'un token FCM spécifique',
        responses={200: FCMTokenSerializer}
    )
    def get(self, request, token_id):
        """
        Récupère les détails d'un token FCM
        """
        try:
            user, auth_error = get_user_from_token(request)
            if auth_error:
                return auth_error
            
            content_type = ContentType.objects.get_for_model(user)
            
            fcm_token = FCMToken.objects.get(
                id=token_id,
                user_type=content_type,
                user_id=user.id
            )
            
            serializer = FCMTokenSerializer(fcm_token)
            
            return Response({
                'success': True,
                'token': serializer.data
            }, status=status.HTTP_200_OK)
            
        except FCMToken.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Token FCM introuvable'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @extend_schema(
        tags=['FCM'],
        summary='Activer/Désactiver un token FCM',
        description='Active ou désactive un token FCM spécifique',
        request={'type': 'object', 'properties': {'is_active': {'type': 'boolean'}}},
        responses={200: {'description': 'Token mis à jour avec succès'}}
    )
    def patch(self, request, token_id):
        """
        Met à jour le statut d'un token FCM
        """
        try:
            user, auth_error = get_user_from_token(request)
            if auth_error:
                return auth_error
            
            content_type = ContentType.objects.get_for_model(user)
            
            fcm_token = FCMToken.objects.get(
                id=token_id,
                user_type=content_type,
                user_id=user.id
            )
            
            is_active = request.data.get('is_active')
            if is_active is not None:
                if is_active:
                    fcm_token.activate()
                else:
                    fcm_token.deactivate()
                
                return Response({
                    'success': True,
                    'message': f'Token FCM {"activé" if is_active else "désactivé"}',
                    'is_active': fcm_token.is_active
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': 'Paramètre is_active requis'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except FCMToken.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Token FCM introuvable'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class FCMTestNotificationView(APIView):
    """
    EXISTING ENDPOINT: POST /api/fcm/test-notification/
    DO NOT MODIFY - Already integrated in production
    """
    
    @extend_schema(
        tags=['FCM'],
        summary='Test de notification FCM',
        description='Envoie une notification de test à l\'utilisateur connecté',
        request={'type': 'object', 'properties': {
            'title': {'type': 'string'},
            'body': {'type': 'string'},
            'data': {'type': 'object'}
        }},
        responses={200: {'description': 'Notification envoyée'}}
    )
    def post(self, request):
        """
        Envoie une notification de test
        """
        try:
            user, auth_error = get_user_from_token(request)
            if auth_error:
                return auth_error
            
            title = request.data.get('title', '🧪 Test de notification')
            body = request.data.get('body', f'Bonjour {user.name}, ceci est une notification de test !')
            data = request.data.get('data', {})
            
            # Envoyer la notification
            success = FCMService.send_notification(
                user=user,
                title=title,
                body=body,
                data=data,
                notification_type='system'
            )
            
            if success:
                return Response({
                    'success': True,
                    'message': 'Notification de test envoyée avec succès',
                    'sent_to_devices': FCMService.get_user_device_count(user)
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': 'Échec de l\'envoi de la notification',
                    'reason': 'Aucun token FCM actif ou erreur serveur'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)