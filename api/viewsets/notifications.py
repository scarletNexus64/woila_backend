from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.contrib.contenttypes.models import ContentType

from ..models import Notification, UserDriver, UserCustomer
from ..serializers import NotificationSerializer, NotificationListSerializer
from ..services.notification_service import NotificationService
# Authentication will be handled manually

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
        from ..models import Token
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
    Vue pour récupérer les notifications d'un utilisateur
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
    Vue pour récupérer uniquement les notifications non lues
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
    Vue pour récupérer, marquer comme lu, ou supprimer une notification
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
    Vue pour marquer toutes les notifications comme lues
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
    Vue pour obtenir les statistiques des notifications
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