from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from api.models import UserDriver, Token
from .models import DriverStatus
import uuid


def get_driver_from_token(request):
    """Récupère le chauffeur depuis le token d'authentification"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token_value = auth_header.split(' ')[1]
    try:
        # Vérifier si c'est un UUID valide
        token_uuid = uuid.UUID(token_value)
        token = Token.objects.get(token=token_uuid, user_type='driver', is_active=True)
        return UserDriver.objects.get(id=token.user_id)
    except (ValueError, Token.DoesNotExist, UserDriver.DoesNotExist):
        return None


@api_view(['POST'])
@csrf_exempt
def toggle_driver_status(request):
    """
    API pour changer le statut du chauffeur (ONLINE/OFFLINE)
    """
    driver = get_driver_from_token(request)
    if not driver:
        return Response(
            {'error': 'Token invalide ou vous devez être un chauffeur'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Récupérer ou créer le statut du chauffeur
    driver_status, created = DriverStatus.objects.get_or_create(
        driver=driver,
        defaults={'status': 'OFFLINE'}
    )
    
    # Basculer le statut
    if driver_status.status == 'OFFLINE':
        driver_status.status = 'ONLINE'
        driver_status.last_online = timezone.now()
        message = 'Vous êtes maintenant en ligne'
    else:
        driver_status.status = 'OFFLINE'
        driver_status.websocket_channel = None
        message = 'Vous êtes maintenant hors ligne'
    
    driver_status.save()
    
    return Response({
        'status': driver_status.status,
        'message': message,
        'last_online': driver_status.last_online
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@csrf_exempt
def get_driver_status(request):
    """
    API pour obtenir le statut actuel du chauffeur
    """
    driver = get_driver_from_token(request)
    if not driver:
        return Response(
            {'error': 'Token invalide ou vous devez être un chauffeur'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        driver_status = DriverStatus.objects.get(driver=driver)
        return Response({
            'status': driver_status.status,
            'last_online': driver_status.last_online,
            'last_location_update': driver_status.last_location_update,
            'current_latitude': driver_status.current_latitude,
            'current_longitude': driver_status.current_longitude
        }, status=status.HTTP_200_OK)
    except DriverStatus.DoesNotExist:
        return Response({
            'status': 'OFFLINE',
            'message': 'Aucun statut trouvé'
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@csrf_exempt
def set_driver_offline(request):
    """
    API pour forcer le passage en mode OFFLINE
    """
    driver = get_driver_from_token(request)
    if not driver:
        return Response(
            {'error': 'Token invalide ou vous devez être un chauffeur'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        driver_status = DriverStatus.objects.get(driver=driver)
        driver_status.status = 'OFFLINE'
        driver_status.websocket_channel = None
        driver_status.save()
        
        return Response({
            'status': 'OFFLINE',
            'message': 'Vous êtes maintenant hors ligne'
        }, status=status.HTTP_200_OK)
    except DriverStatus.DoesNotExist:
        return Response({
            'status': 'OFFLINE',
            'message': 'Déjà hors ligne'
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@csrf_exempt
def set_driver_online(request):
    """
    API pour forcer le passage en mode ONLINE
    """
    driver = get_driver_from_token(request)
    if not driver:
        return Response(
            {'error': 'Token invalide ou vous devez être un chauffeur'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    driver_status, created = DriverStatus.objects.get_or_create(
        driver=driver,
        defaults={'status': 'ONLINE', 'last_online': timezone.now()}
    )
    
    if not created:
        driver_status.status = 'ONLINE'
        driver_status.last_online = timezone.now()
        driver_status.save()
    
    return Response({
        'status': 'ONLINE',
        'message': 'Vous êtes maintenant en ligne',
        'last_online': driver_status.last_online
    }, status=status.HTTP_200_OK)