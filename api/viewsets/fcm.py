"""
ViewSets pour la gestion des tokens FCM
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.contrib.contenttypes.models import ContentType

from ..models import FCMToken, UserDriver, UserCustomer
from ..serializers import FCMTokenRegisterSerializer, FCMTokenSerializer, FCMTokenListSerializer
from ..services.fcm_service import FCMService

# Fonction helper pour l'authentification (reprise des notifications)
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
class FCMTokenRegisterView(APIView):
    """
    Vue pour enregistrer un token FCM
    """
    
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
            
            fcm_token_value = serializer.validated_data['fcm_token']
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
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class FCMTokenUnregisterView(APIView):
    """
    Vue pour supprimer un token FCM
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
    Vue pour lister les tokens FCM d'un utilisateur
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
    Vue pour les détails d'un token FCM spécifique
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
    Vue pour tester l'envoi d'une notification FCM
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