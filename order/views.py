"""
Views/Endpoints pour le module de commande VTC
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter
from decimal import Decimal
import logging
import asyncio
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from api.models import UserDriver, UserCustomer, Token, City, VipZone
from .models import (
    Order, DriverStatus, OrderTracking, PaymentMethod,
    Rating, TripTracking, DriverPool
)
from .serializers import (
    PaymentMethodSerializer, DriverStatusSerializer, UpdateLocationSerializer,
    SearchDriversSerializer, EstimatePriceSerializer, CreateOrderSerializer,
    OrderSerializer, OrderListSerializer, RatingSerializer, CreateRatingSerializer,
    TripTrackingSerializer, OrderTrackingSerializer, DriverPoolSerializer,
    CancelOrderSerializer, CompleteOrderSerializer, ProcessPaymentSerializer
)
from .services import (
    PricingService, OrderService, DriverPoolService,
    PaymentService, TrackingService
)

logger = logging.getLogger(__name__)


# ============= HELPER FUNCTIONS =============

def get_user_from_token(request):
    """Récupère l'utilisateur depuis le token d'authentification"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None, None
    
    token_value = auth_header.split(' ')[1]
    try:
        token = Token.objects.get(token=token_value, is_active=True)
        if token.user_type == 'driver':
            return UserDriver.objects.get(id=token.user_id), 'driver'
        elif token.user_type == 'customer':
            return UserCustomer.objects.get(id=token.user_id), 'customer'
    except (Token.DoesNotExist, UserDriver.DoesNotExist, UserCustomer.DoesNotExist):
        pass
    
    return None, None


def get_driver_from_token(request):
    """Récupère le chauffeur depuis le token"""
    user, user_type = get_user_from_token(request)
    if user_type == 'driver':
        return user
    return None


def get_customer_from_token(request):
    """Récupère le client depuis le token"""
    user, user_type = get_user_from_token(request)
    if user_type == 'customer':
        return user
    return None


def notify_drivers_new_order(order, pool_entries):
    """Envoie une notification WebSocket ET FCM à tous les chauffeurs concernés par une commande"""
    from api.services.fcm_service import FCMService
    import json
    
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            logger.warning("Channel layer non disponible - notifications WebSocket non envoyées")
        
        # Préparer les données de la commande pour les chauffeurs - Format compatible Flutter
        order_data = {
            'id': str(order.id),
            'customer_id': str(order.customer.id),  # Ajouter customer_id
            'customer_name': f"Client {order.customer.phone_number}",
            'customer_phone': order.customer.phone_number,
            'pickup_address': order.pickup_address,
            'pickup_latitude': float(order.pickup_latitude),
            'pickup_longitude': float(order.pickup_longitude),
            'destination_address': order.destination_address,
            'destination_latitude': float(order.destination_latitude),
            'destination_longitude': float(order.destination_longitude),
            'vehicle_type': order.vehicle_type.name if order.vehicle_type else 'Standard',
            'estimated_distance_km': float(order.estimated_distance_km or 0),  # Match exact field name
            'total_price': float(order.total_price),
            'customer_notes': order.customer_notes or '',
            'timeout_seconds': 30,  # 30 secondes pour répondre
            'created_at': order.created_at.isoformat(),
        }
        
        # Envoyer la notification à chaque chauffeur du pool
        websocket_notifications_sent = 0
        fcm_notifications_sent = 0
        
        for pool_entry in pool_entries:
            try:
                driver = pool_entry.driver
                driver_id = driver.id
                driver_group_name = f'driver_{driver_id}'
                
                logger.info(f"📤 Envoi notification → Chauffeur {driver_id}")
                
                # 1. Envoyer via WebSocket
                if channel_layer:
                    try:
                        async_to_sync(channel_layer.group_send)(
                            driver_group_name,
                            {
                                'type': 'order_request',
                                'order_data': order_data
                            }
                        )
                        websocket_notifications_sent += 1
                        logger.info(f"✅ WebSocket envoyé au chauffeur {driver_id}")
                    except Exception as ws_error:
                        logger.error(f"❌ Erreur WebSocket chauffeur {driver_id}: {ws_error}")
                
                # 2. Envoyer via FCM (NOUVEAU!)
                try:
                    customer_name = order_data['customer_name']
                    distance = order_data['estimated_distance_km']
                    price = order_data['total_price']
                    
                    fcm_success = FCMService.send_notification(
                        user=driver,
                        title="🚗 Nouvelle commande disponible!",
                        body=f"{customer_name} • {distance:.1f} km • {price:.0f} FCFA",
                        data={
                            'notification_type': 'new_order',
                            'order_id': str(order.id),
                            'order_data': json.dumps(order_data),  # Inclure toutes les données
                            'action_required': 'accept_or_decline',
                            'timeout_seconds': '30'
                        },
                        notification_type='new_order'
                    )
                    
                    if fcm_success:
                        fcm_notifications_sent += 1
                        logger.info(f"✅ FCM envoyé au chauffeur {driver_id}")
                    else:
                        logger.warning(f"⚠️ FCM échoué pour chauffeur {driver_id}")
                        
                except Exception as fcm_error:
                    logger.error(f"❌ Erreur FCM chauffeur {driver_id}: {fcm_error}")
                
            except Exception as driver_error:
                logger.error(f"❌ Erreur notification chauffeur {pool_entry.driver.id}: {driver_error}")
                continue
        
        logger.info(f"📊 Notifications envoyées: WebSocket {websocket_notifications_sent}/{len(pool_entries)}, FCM {fcm_notifications_sent}/{len(pool_entries)} chauffeurs")
        return websocket_notifications_sent + fcm_notifications_sent
        
    except Exception as e:
        logger.error(f"❌ Erreur générale notifications: {e}")
        return 0


# ============= DRIVER ENDPOINTS =============

@extend_schema(
    tags=['Driver'],
    summary='Basculer le statut en ligne/hors ligne',
    description='Permet au chauffeur de passer en ligne ou hors ligne'
)
@api_view(['POST'])
def toggle_driver_status(request):
    """Toggle driver online/offline status"""
    driver = get_driver_from_token(request)
    if not driver:
        return Response(
            {'error': 'Authentification requise en tant que chauffeur'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        driver_status, created = DriverStatus.objects.get_or_create(
            driver=driver,
            defaults={'status': 'OFFLINE'}
        )
        
        if driver_status.status == 'OFFLINE':
            driver_status.go_online()
            message = 'Vous êtes maintenant en ligne'
            new_status = 'ONLINE'
            
            # Démarrer automatiquement la diffusion GPS via WebSocket
            _start_driver_location_broadcasting(driver.id)
        else:
            driver_status.go_offline()
            message = 'Vous êtes maintenant hors ligne'
            new_status = 'OFFLINE'
            
            # Arrêter la diffusion GPS
            _stop_driver_location_broadcasting(driver.id)
        
        return Response({
            'success': True,
            'message': message,
            'status': new_status,
            'data': DriverStatusSerializer(driver_status).data
        })
        
    except Exception as e:
        logger.error(f"Erreur toggle status: {str(e)}")
        return Response(
            {'error': 'Erreur lors du changement de statut'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['Driver'],
    summary='Mettre à jour la position GPS',
    description='Met à jour la position actuelle du chauffeur'
)
@api_view(['POST'])
def update_driver_location(request):
    """Update driver GPS location"""
    driver = get_driver_from_token(request)
    if not driver:
        return Response(
            {'error': 'Authentification requise en tant que chauffeur'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    serializer = UpdateLocationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        driver_status = DriverStatus.objects.get(driver=driver)
        
        # Mettre à jour la position
        driver_status.current_latitude = serializer.validated_data['latitude']
        driver_status.current_longitude = serializer.validated_data['longitude']
        driver_status.last_location_update = timezone.now()
        driver_status.save()
        
        # Si le chauffeur est en course, enregistrer dans TripTracking
        current_order = Order.objects.filter(
            driver=driver,
            status='IN_PROGRESS'
        ).first()
        
        if current_order:
            tracking_service = TrackingService()
            tracking_service.record_position(
                order=current_order,
                driver=driver,
                latitude=float(serializer.validated_data['latitude']),
                longitude=float(serializer.validated_data['longitude']),
                speed_kmh=serializer.validated_data.get('speed_kmh'),
                heading=serializer.validated_data.get('heading'),
                accuracy=serializer.validated_data.get('accuracy')
            )
        
        return Response({
            'success': True,
            'message': 'Position mise à jour',
            'current_location': {
                'latitude': float(driver_status.current_latitude),
                'longitude': float(driver_status.current_longitude),
                'last_update': driver_status.last_location_update.isoformat()
            }
        })
        
    except DriverStatus.DoesNotExist:
        return Response(
            {'error': 'Statut chauffeur non trouvé'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Erreur update location: {str(e)}")
        return Response(
            {'error': 'Erreur lors de la mise à jour de la position'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['Driver'],
    summary='Accepter une commande',
    description='Permet au chauffeur d\'accepter une commande proposée'
)
@api_view(['POST'])
def accept_order(request, order_id):
    """Accept an order request"""
    driver = get_driver_from_token(request)
    if not driver:
        return Response(
            {'error': 'Authentification requise en tant que chauffeur'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        order = Order.objects.get(id=order_id, status='PENDING')
        
        # Vérifier si le chauffeur est dans le pool
        pool_entry = DriverPool.objects.filter(
            order=order,
            driver=driver,
            request_status='PENDING'
        ).first()
        
        if not pool_entry:
            return Response(
                {'error': 'Vous n\'êtes pas autorisé à accepter cette commande'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Traiter l'acceptation
        pool_service = DriverPoolService()
        success = pool_service.handle_driver_response(pool_entry, accepted=True)
        
        if success:
            # Rafraîchir l'ordre
            order.refresh_from_db()
            
            return Response({
                'success': True,
                'message': 'Commande acceptée avec succès',
                'order': OrderSerializer(order).data
            })
        else:
            return Response(
                {'error': 'Impossible d\'accepter la commande'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Order.DoesNotExist:
        return Response(
            {'error': 'Commande non trouvée ou déjà acceptée'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Erreur accept order: {str(e)}")
        return Response(
            {'error': 'Erreur lors de l\'acceptation'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['Driver'],
    summary='Refuser une commande',
    description='Permet au chauffeur de refuser une commande proposée'
)
@api_view(['POST'])
def reject_order(request, order_id):
    """Reject an order request"""
    driver = get_driver_from_token(request)
    if not driver:
        return Response(
            {'error': 'Authentification requise en tant que chauffeur'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    reason = request.data.get('reason', 'Non spécifié')
    
    try:
        order = Order.objects.get(id=order_id, status='PENDING')
        
        # Vérifier si le chauffeur est dans le pool
        pool_entry = DriverPool.objects.filter(
            order=order,
            driver=driver,
            request_status='PENDING'
        ).first()
        
        if not pool_entry:
            return Response(
                {'error': 'Vous n\'êtes pas autorisé à refuser cette commande'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Traiter le refus
        pool_service = DriverPoolService()
        pool_service.handle_driver_response(pool_entry, accepted=False, rejection_reason=reason)
        
        return Response({
            'success': True,
            'message': 'Commande refusée'
        })
        
    except Order.DoesNotExist:
        return Response(
            {'error': 'Commande non trouvée'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Erreur reject order: {str(e)}")
        return Response(
            {'error': 'Erreur lors du refus'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['Driver'],
    summary='Signaler arrivée sur place',
    description='Le chauffeur signale qu\'il est arrivé au point de pickup'
)
@api_view(['POST'])
def driver_arrived(request, order_id):
    """Mark driver as arrived at pickup location"""
    driver = get_driver_from_token(request)
    if not driver:
        return Response(
            {'error': 'Authentification requise en tant que chauffeur'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        order = Order.objects.get(id=order_id, driver=driver, status='ACCEPTED')
        
        order_service = OrderService()
        success = order_service.update_order_status(
            order, 'DRIVER_ARRIVED', actor_driver=driver
        )
        
        if success:
            return Response({
                'success': True,
                'message': 'Arrivée enregistrée',
                'order': OrderSerializer(order).data
            })
        else:
            return Response(
                {'error': 'Transition de statut invalide'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Order.DoesNotExist:
        return Response(
            {'error': 'Commande non trouvée'},
            status=status.HTTP_404_NOT_FOUND
        )


@extend_schema(
    tags=['Driver'],
    summary='Démarrer la course',
    description='Démarre la course après que le client soit monté'
)
@api_view(['POST'])
def start_trip(request, order_id):
    """Start the trip"""
    driver = get_driver_from_token(request)
    if not driver:
        return Response(
            {'error': 'Authentification requise en tant que chauffeur'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        order = Order.objects.get(id=order_id, driver=driver, status='DRIVER_ARRIVED')
        
        order_service = OrderService()
        success = order_service.update_order_status(
            order, 'IN_PROGRESS', actor_driver=driver
        )
        
        if success:
            return Response({
                'success': True,
                'message': 'Course démarrée',
                'order': OrderSerializer(order).data
            })
        else:
            return Response(
                {'error': 'Transition de statut invalide'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Order.DoesNotExist:
        return Response(
            {'error': 'Commande non trouvée'},
            status=status.HTTP_404_NOT_FOUND
        )


@extend_schema(
    tags=['Driver'],
    summary='Terminer la course',
    description='Termine la course et calcule le prix final'
)
@api_view(['POST'])
def complete_trip(request, order_id):
    """Complete the trip"""
    driver = get_driver_from_token(request)
    if not driver:
        return Response(
            {'error': 'Authentification requise en tant que chauffeur'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    serializer = CompleteOrderSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            order = Order.objects.get(id=order_id, driver=driver, status='IN_PROGRESS')
            
            # Mettre à jour les données de la course
            order.actual_distance_km = serializer.validated_data['actual_distance_km']
            order.waiting_time = serializer.validated_data.get('waiting_time', 0)
            order.driver_notes = serializer.validated_data.get('driver_notes', '')
            
            # Calculer le prix final
            pricing_service = PricingService()
            final_price = pricing_service.update_final_price(order)
            
            # Mettre à jour le statut
            order_service = OrderService()
            success = order_service.update_order_status(
                order, 'COMPLETED', actor_driver=driver
            )
            
            if success:
                # Mettre à jour les stats du chauffeur
                driver_status = DriverStatus.objects.get(driver=driver)
                driver_status.total_orders_today += 1
                driver_status.status = 'ONLINE'  # Retour en ligne
                driver_status.save()
                
                return Response({
                    'success': True,
                    'message': 'Course terminée',
                    'final_price': float(final_price),
                    'order': OrderSerializer(order).data
                })
            else:
                return Response(
                    {'error': 'Impossible de terminer la course'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
    except Order.DoesNotExist:
        return Response(
            {'error': 'Commande non trouvée'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Erreur complete trip: {str(e)}")
        return Response(
            {'error': 'Erreur lors de la finalisation'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['Driver'],
    summary='Obtenir la commande en cours',
    description='Récupère la commande actuellement en cours du chauffeur'
)
@api_view(['GET'])
def get_driver_current_order(request):
    """Get driver's current active order"""
    driver = get_driver_from_token(request)
    if not driver:
        return Response(
            {'error': 'Authentification requise en tant que chauffeur'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    current_order = Order.objects.filter(
        driver=driver,
        status__in=['ACCEPTED', 'DRIVER_ARRIVED', 'IN_PROGRESS']
    ).first()
    
    if current_order:
        return Response({
            'success': True,
            'order': OrderSerializer(current_order).data
        })
    else:
        return Response({
            'success': True,
            'order': None,
            'message': 'Aucune commande en cours'
        })


@extend_schema(
    tags=['Driver'],
    summary='Historique des courses du chauffeur',
    description='Récupère l\'historique des courses du chauffeur'
)
@api_view(['GET'])
def get_driver_order_history(request):
    """Get driver's order history"""
    driver = get_driver_from_token(request)
    if not driver:
        return Response(
            {'error': 'Authentification requise en tant que chauffeur'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Paramètres de pagination
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    offset = (page - 1) * page_size
    
    # Filtres optionnels
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    status_filter = request.GET.get('status')
    
    query = Order.objects.filter(driver=driver)
    
    if date_from:
        query = query.filter(created_at__gte=date_from)
    if date_to:
        query = query.filter(created_at__lte=date_to)
    if status_filter:
        query = query.filter(status=status_filter)
    
    total_count = query.count()
    orders = query.order_by('-created_at')[offset:offset + page_size]
    
    return Response({
        'success': True,
        'total': total_count,
        'page': page,
        'page_size': page_size,
        'orders': OrderListSerializer(orders, many=True).data
    })


# ============= CUSTOMER ENDPOINTS =============

@extend_schema(
    tags=['Customer'],
    summary='Rechercher des chauffeurs disponibles',
    description='Recherche les chauffeurs disponibles autour du point de pickup'
)
@api_view(['POST'])
def search_drivers(request):
    """Search for available drivers"""
    customer = get_customer_from_token(request)
    if not customer:
        return Response(
            {'error': 'Authentification requise en tant que client'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    serializer = SearchDriversSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        order_service = OrderService()
        
        # Trouver les chauffeurs proches
        nearby_drivers = order_service.find_nearby_drivers(
            pickup_lat=float(serializer.validated_data['pickup_latitude']),
            pickup_lng=float(serializer.validated_data['pickup_longitude']),
            vehicle_type_id=serializer.validated_data.get('vehicle_type_id'),
            radius_km=serializer.validated_data.get('radius_km', 5)
        )
        
        # Obtenir les types de véhicules disponibles
        vehicle_types = order_service.get_available_vehicle_types(
            pickup_lat=float(serializer.validated_data['pickup_latitude']),
            pickup_lng=float(serializer.validated_data['pickup_longitude']),
            radius_km=serializer.validated_data.get('radius_km', 5)
        )
        
        return Response({
            'success': True,
            'drivers_found': len(nearby_drivers),
            'vehicle_types': vehicle_types,
            'drivers': nearby_drivers[:10]  # Limiter pour la réponse
        })
        
    except Exception as e:
        logger.error(f"Erreur search drivers: {str(e)}")
        return Response(
            {'error': 'Erreur lors de la recherche'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['Customer'],
    summary='Estimer le prix d\'une course',
    description='Calcule une estimation du prix pour une course'
)
@api_view(['POST'])
def estimate_price(request):
    """Estimate trip price"""
    customer = get_customer_from_token(request)
    if not customer:
        return Response(
            {'error': 'Authentification requise en tant que client'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    serializer = EstimatePriceSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        order_service = OrderService()
        pricing_service = PricingService()
        
        # Calculer la distance
        distance = order_service.calculate_real_distance(
            float(serializer.validated_data['pickup_latitude']),
            float(serializer.validated_data['pickup_longitude']),
            float(serializer.validated_data['destination_latitude']),
            float(serializer.validated_data['destination_longitude'])
        )
        
        # Estimer le prix
        price_range = pricing_service.estimate_price_range(
            vehicle_type_id=serializer.validated_data['vehicle_type_id'],
            city_id=serializer.validated_data['city_id'],
            estimated_distance_km=distance,
            vip_zone_id=serializer.validated_data.get('vip_zone_id')
        )
        
        return Response({
            'success': True,
            'distance_km': round(distance, 2),
            'price_estimate': price_range
        })
        
    except Exception as e:
        logger.error(f"Erreur estimate price: {str(e)}")
        return Response(
            {'error': 'Erreur lors de l\'estimation'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['Customer'],
    summary='Créer une commande',
    description='Crée une nouvelle commande de VTC'
)
@api_view(['POST'])
def create_order(request):
    """Create a new order"""
    customer = get_customer_from_token(request)
    if not customer:
        return Response(
            {'error': 'Authentification requise en tant que client'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    serializer = CreateOrderSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            order_service = OrderService()
            
            # Créer la commande
            order = order_service.create_order(
                customer_id=customer.id,
                order_data=serializer.validated_data
            )
            
            # Créer le pool de chauffeurs
            pool_service = DriverPoolService()
            pool_entries = pool_service.create_driver_pool(order)
            
            if not pool_entries:
                order.status = 'CANCELLED'
                order.cancellation_reason = 'Aucun chauffeur disponible'
                order.cancelled_at = timezone.now()
                order.save()
                
                return Response({
                    'success': False,
                    'message': 'Aucun chauffeur disponible dans votre zone',
                    'order_id': str(order.id)
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Notifier les chauffeurs via WebSocket
            notifications_sent = notify_drivers_new_order(order, pool_entries)
            logger.info(f"🔔 Commande {order.id}: {notifications_sent} notifications WebSocket envoyées")
            
            return Response({
                'success': True,
                'message': 'Commande créée, recherche de chauffeur en cours',
                'order': OrderSerializer(order).data,
                'drivers_contacted': len(pool_entries),
                'notifications_sent': notifications_sent
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        logger.error(f"Erreur create order: {str(e)}")
        return Response(
            {'error': 'Erreur lors de la création de la commande'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['Customer'],
    summary='Annuler une commande',
    description='Permet au client d\'annuler une commande'
)
@api_view(['POST'])
def cancel_order(request, order_id):
    """Cancel an order"""
    customer = get_customer_from_token(request)
    if not customer:
        return Response(
            {'error': 'Authentification requise en tant que client'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    serializer = CancelOrderSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        order = Order.objects.get(
            id=order_id,
            customer=customer,
            status__in=['PENDING', 'ACCEPTED', 'DRIVER_ARRIVED']
        )
        
        # Vérifier les frais d'annulation
        from datetime import timedelta
        free_cancellation_time = 5  # minutes
        
        if order.accepted_at:
            time_since_accept = timezone.now() - order.accepted_at
            if time_since_accept > timedelta(minutes=free_cancellation_time):
                # TODO: Appliquer des frais d'annulation
                pass
        
        order_service = OrderService()
        success = order_service.update_order_status(
            order, 'CANCELLED',
            actor_customer=customer,
            notes=serializer.validated_data['reason']
        )
        
        if success:
            # Libérer le chauffeur si assigné
            if order.driver:
                driver_status = DriverStatus.objects.get(driver=order.driver)
                driver_status.status = 'ONLINE'
                driver_status.save()
            
            return Response({
                'success': True,
                'message': 'Commande annulée',
                'order': OrderSerializer(order).data
            })
        else:
            return Response(
                {'error': 'Impossible d\'annuler cette commande'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Order.DoesNotExist:
        return Response(
            {'error': 'Commande non trouvée'},
            status=status.HTTP_404_NOT_FOUND
        )


@extend_schema(
    tags=['Customer'],
    summary='Suivre une commande',
    description='Obtient les détails et le statut actuel d\'une commande'
)
@api_view(['GET'])
def track_order(request, order_id):
    """Track order status and driver location"""
    customer = get_customer_from_token(request)
    if not customer:
        return Response(
            {'error': 'Authentification requise en tant que client'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        order = Order.objects.get(id=order_id, customer=customer)
        
        # Obtenir la position actuelle du chauffeur si en course
        driver_location = None
        if order.driver and order.status in ['ACCEPTED', 'DRIVER_ARRIVED', 'IN_PROGRESS']:
            driver_status = DriverStatus.objects.get(driver=order.driver)
            driver_location = {
                'latitude': float(driver_status.current_latitude) if driver_status.current_latitude else None,
                'longitude': float(driver_status.current_longitude) if driver_status.current_longitude else None,
                'last_update': driver_status.last_location_update.isoformat() if driver_status.last_location_update else None
            }
        
        # Obtenir les événements de tracking
        tracking_events = OrderTracking.objects.filter(
            order=order
        ).order_by('-created_at')[:10]
        
        return Response({
            'success': True,
            'order': OrderSerializer(order).data,
            'driver_location': driver_location,
            'tracking_events': OrderTrackingSerializer(tracking_events, many=True).data
        })
        
    except Order.DoesNotExist:
        return Response(
            {'error': 'Commande non trouvée'},
            status=status.HTTP_404_NOT_FOUND
        )


@extend_schema(
    tags=['Customer'],
    summary='Noter une course',
    description='Permet au client de noter le chauffeur après une course'
)
@api_view(['POST'])
def rate_order(request, order_id):
    """Rate a completed order"""
    customer = get_customer_from_token(request)
    if not customer:
        return Response(
            {'error': 'Authentification requise en tant que client'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    serializer = CreateRatingSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        order = Order.objects.get(
            id=order_id,
            customer=customer,
            status='COMPLETED'
        )
        
        # Vérifier si déjà noté
        existing_rating = Rating.objects.filter(
            order=order,
            rating_type='CUSTOMER_TO_DRIVER'
        ).exists()
        
        if existing_rating:
            return Response(
                {'error': 'Cette course a déjà été notée'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Créer la notation
        rating = Rating.objects.create(
            order=order,
            rating_type='CUSTOMER_TO_DRIVER',
            rated_driver=order.driver,
            score=serializer.validated_data['score'],
            comment=serializer.validated_data.get('comment', ''),
            punctuality=serializer.validated_data.get('punctuality'),
            driving_quality=serializer.validated_data.get('driving_quality'),
            vehicle_cleanliness=serializer.validated_data.get('vehicle_cleanliness'),
            communication=serializer.validated_data.get('communication'),
            tags=serializer.validated_data.get('tags', []),
            is_anonymous=serializer.validated_data.get('is_anonymous', False)
        )
        
        # Mettre à jour la note sur la commande
        order.driver_rating = serializer.validated_data['score']
        order.save()
        
        return Response({
            'success': True,
            'message': 'Merci pour votre évaluation',
            'rating': RatingSerializer(rating).data
        }, status=status.HTTP_201_CREATED)
        
    except Order.DoesNotExist:
        return Response(
            {'error': 'Commande non trouvée ou non terminée'},
            status=status.HTTP_404_NOT_FOUND
        )


@extend_schema(
    tags=['Customer'],
    summary='Historique des commandes du client',
    description='Récupère l\'historique des commandes du client'
)
@api_view(['GET'])
def get_customer_order_history(request):
    """Get customer's order history"""
    customer = get_customer_from_token(request)
    if not customer:
        return Response(
            {'error': 'Authentification requise en tant que client'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Paramètres de pagination
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    offset = (page - 1) * page_size
    
    # Filtres optionnels
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    status_filter = request.GET.get('status')
    
    query = Order.objects.filter(customer=customer)
    
    if date_from:
        query = query.filter(created_at__gte=date_from)
    if date_to:
        query = query.filter(created_at__lte=date_to)
    if status_filter:
        query = query.filter(status=status_filter)
    
    total_count = query.count()
    orders = query.order_by('-created_at')[offset:offset + page_size]
    
    return Response({
        'success': True,
        'total': total_count,
        'page': page,
        'page_size': page_size,
        'orders': OrderListSerializer(orders, many=True).data
    })


# ============= PAYMENT ENDPOINTS =============

@extend_schema(
    tags=['Payment'],
    summary='Traiter un paiement',
    description='Traite le paiement d\'une commande terminée'
)
@api_view(['POST'])
def process_payment(request, order_id):
    """Process order payment"""
    user, user_type = get_user_from_token(request)
    if not user:
        return Response(
            {'error': 'Authentification requise'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    serializer = ProcessPaymentSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Vérifier l'accès à la commande
        if user_type == 'customer':
            order = Order.objects.get(id=order_id, customer=user)
        else:
            return Response(
                {'error': 'Seul le client peut payer la commande'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Vérifier que la commande est terminée
        if order.status != 'COMPLETED':
            return Response(
                {'error': 'La commande doit être terminée pour être payée'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Traiter le paiement
        payment_service = PaymentService()
        result = payment_service.process_payment(
            order,
            payment_method_id=serializer.validated_data.get('payment_method_id')
        )
        
        if result['success']:
            return Response({
                'success': True,
                'message': result['message'],
                'payment_status': order.payment_status,
                'transaction': result
            })
        else:
            return Response({
                'success': False,
                'error': result['message'],
                'status': result.get('status')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Order.DoesNotExist:
        return Response(
            {'error': 'Commande non trouvée'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Erreur process payment: {str(e)}")
        return Response(
            {'error': 'Erreur lors du traitement du paiement'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============= COMMON ENDPOINTS =============

@extend_schema(
    tags=['Common'],
    summary='Liste des méthodes de paiement',
    description='Récupère toutes les méthodes de paiement disponibles'
)
@api_view(['GET'])
def get_payment_methods(request):
    """Get available payment methods"""
    payment_methods = PaymentMethod.objects.filter(is_active=True)
    return Response({
        'success': True,
        'payment_methods': PaymentMethodSerializer(payment_methods, many=True).data
    })


@extend_schema(
    tags=['Common'],
    summary='Détails d\'une commande',
    description='Récupère les détails complets d\'une commande'
)
@api_view(['GET'])
def get_order_details(request, order_id):
    """Get order details"""
    user, user_type = get_user_from_token(request)
    if not user:
        return Response(
            {'error': 'Authentification requise'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        # Vérifier l'accès selon le type d'utilisateur
        if user_type == 'customer':
            order = Order.objects.get(id=order_id, customer=user)
        elif user_type == 'driver':
            order = Order.objects.get(id=order_id, driver=user)
        else:
            return Response(
                {'error': 'Non autorisé'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return Response({
            'success': True,
            'order': OrderSerializer(order).data
        })
        
    except Order.DoesNotExist:
        return Response(
            {'error': 'Commande non trouvée'},
            status=status.HTTP_404_NOT_FOUND
        )


@extend_schema(
    tags=['Common'],
    summary='Types de véhicules disponibles',
    description='Récupère les types de véhicules disponibles dans une zone'
)
@api_view(['POST'])
def get_available_vehicle_types(request):
    """Get available vehicle types in an area"""
    data = request.data
    
    if not all(k in data for k in ['pickup_latitude', 'pickup_longitude']):
        return Response(
            {'error': 'Coordonnées de pickup requises'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        order_service = OrderService()
        vehicle_types = order_service.get_available_vehicle_types(
            pickup_lat=float(data['pickup_latitude']),
            pickup_lng=float(data['pickup_longitude']),
            radius_km=data.get('radius_km', 5)
        )
        
        return Response({
            'success': True,
            'vehicle_types': vehicle_types
        })
        
    except Exception as e:
        logger.error(f"Erreur get vehicle types: {str(e)}")
        return Response(
            {'error': 'Erreur lors de la récupération'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============= STATUS ENDPOINTS (Legacy) =============

@api_view(['GET'])
def get_driver_status(request):
    """Get current driver status (legacy)"""
    driver = get_driver_from_token(request)
    if not driver:
        return Response(
            {'error': 'Authentification requise en tant que chauffeur'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        driver_status = DriverStatus.objects.get(driver=driver)
        return Response(DriverStatusSerializer(driver_status).data)
    except DriverStatus.DoesNotExist:
        return Response(
            {'error': 'Statut non trouvé'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
def set_driver_online(request):
    """Set driver status to online (legacy)"""
    driver = get_driver_from_token(request)
    if not driver:
        return Response(
            {'error': 'Authentification requise en tant que chauffeur'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    driver_status, created = DriverStatus.objects.get_or_create(driver=driver)
    driver_status.go_online()
    
    return Response({
        'success': True,
        'message': 'Vous êtes maintenant en ligne',
        'status': DriverStatusSerializer(driver_status).data
    })


@api_view(['POST'])
def set_driver_offline(request):
    """Set driver status to offline (legacy)"""
    driver = get_driver_from_token(request)
    if not driver:
        return Response(
            {'error': 'Authentification requise en tant que chauffeur'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    driver_status, created = DriverStatus.objects.get_or_create(driver=driver)
    driver_status.go_offline()
    
    return Response({
        'success': True,
        'message': 'Vous êtes maintenant hors ligne',
        'status': DriverStatusSerializer(driver_status).data
    })


# ============= SEARCH ENDPOINTS =============

@extend_schema(
    tags=['Search'],
    summary='Rechercher une ville par nom',
    description='Recherche une ville par son nom pour obtenir son ID et ses informations tarifaires',
    parameters=[
        OpenApiParameter(
            name='name',
            type=str,
            location=OpenApiParameter.QUERY,
            description='Nom de la ville à rechercher (ex: "Yaoundé", "Dakar")',
            required=True
        ),
        OpenApiParameter(
            name='country',
            type=str,
            location=OpenApiParameter.QUERY,
            description='Nom du pays pour filtrer (optionnel)',
            required=False
        )
    ]
)
@api_view(['GET'])
def search_city_by_name(request):
    """Recherche une ville par son nom"""
    city_name = request.GET.get('name')
    country_name = request.GET.get('country')
    
    if not city_name:
        return Response(
            {'error': 'Le paramètre "name" est requis'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Construire la requête
        query = City.objects.filter(
            name__icontains=city_name,
            active=True
        ).select_related('country')
        
        # Filtrer par pays si fourni
        if country_name:
            query = query.filter(country__name__icontains=country_name)
        
        # Exécuter la recherche
        cities = query[:10]  # Limiter à 10 résultats
        
        if not cities:
            return Response({
                'success': True,
                'message': 'Aucune ville trouvée',
                'cities': []
            })
        
        # Formatter les résultats
        cities_data = []
        for city in cities:
            cities_data.append({
                'id': city.id,
                'name': city.name,
                'country': city.country.name,
                'prix_jour': float(city.prix_jour),
                'prix_nuit': float(city.prix_nuit),
                'full_name': f"{city.name} ({city.country.name})"
            })
        
        return Response({
            'success': True,
            'message': f'{len(cities)} ville(s) trouvée(s)',
            'cities': cities_data
        })
        
    except Exception as e:
        logger.error(f"Erreur recherche ville: {str(e)}")
        return Response(
            {'error': 'Erreur lors de la recherche'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['Search'],
    summary='Rechercher une zone VIP par nom',
    description='Recherche une zone VIP par son nom pour obtenir son ID et ses informations tarifaires',
    parameters=[
        OpenApiParameter(
            name='name',
            type=str,
            location=OpenApiParameter.QUERY,
            description='Nom de la zone VIP à rechercher (ex: "Plateau", "Airport")',
            required=True
        )
    ]
)
@api_view(['GET'])
def search_vip_zone_by_name(request):
    """Recherche une zone VIP par son nom"""
    zone_name = request.GET.get('name')
    
    if not zone_name:
        return Response(
            {'error': 'Le paramètre "name" est requis'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Rechercher les zones VIP
        zones = VipZone.objects.filter(
            name__icontains=zone_name,
            active=True
        ).prefetch_related('kilometer_rules')[:10]  # Limiter à 10 résultats
        
        if not zones:
            return Response({
                'success': True,
                'message': 'Aucune zone VIP trouvée',
                'zones': []
            })
        
        # Formatter les résultats
        zones_data = []
        for zone in zones:
            # Récupérer les règles kilométriques actives
            km_rules = []
            for rule in zone.kilometer_rules.filter(active=True).order_by('min_kilometers'):
                km_rules.append({
                    'min_kilometers': float(rule.min_kilometers),
                    'prix_jour_per_km': float(rule.prix_jour_per_km),
                    'prix_nuit_per_km': float(rule.prix_nuit_per_km)
                })
            
            zones_data.append({
                'id': zone.id,
                'name': zone.name,
                'prix_jour': float(zone.prix_jour),
                'prix_nuit': float(zone.prix_nuit),
                'kilometer_rules': km_rules
            })
        
        return Response({
            'success': True,
            'message': f'{len(zones)} zone(s) VIP trouvée(s)',
            'zones': zones_data
        })
        
    except Exception as e:
        logger.error(f"Erreur recherche zone VIP: {str(e)}")
        return Response(
            {'error': 'Erreur lors de la recherche'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['Search'],
    summary='Lister toutes les villes actives',
    description='Récupère la liste complète des villes actives avec pagination'
)
@api_view(['GET'])
def list_cities(request):
    """Liste toutes les villes actives"""
    try:
        # Paramètres de pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 50))
        offset = (page - 1) * page_size
        
        # Récupérer les villes
        total_count = City.objects.filter(active=True).count()
        cities = City.objects.filter(active=True).select_related('country')[offset:offset + page_size]
        
        cities_data = []
        for city in cities:
            cities_data.append({
                'id': city.id,
                'name': city.name,
                'country': city.country.name,
                'prix_jour': float(city.prix_jour),
                'prix_nuit': float(city.prix_nuit),
                'full_name': f"{city.name} ({city.country.name})"
            })
        
        return Response({
            'success': True,
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'cities': cities_data
        })
        
    except Exception as e:
        logger.error(f"Erreur liste villes: {str(e)}")
        return Response(
            {'error': 'Erreur lors de la récupération'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['Search'],
    summary='Lister toutes les zones VIP actives',
    description='Récupère la liste complète des zones VIP actives avec leurs règles kilométriques'
)
@api_view(['GET'])
def list_vip_zones(request):
    """Liste toutes les zones VIP actives"""
    try:
        zones = VipZone.objects.filter(active=True).prefetch_related('kilometer_rules')
        
        zones_data = []
        for zone in zones:
            # Récupérer les règles kilométriques actives
            km_rules = []
            for rule in zone.kilometer_rules.filter(active=True).order_by('min_kilometers'):
                km_rules.append({
                    'min_kilometers': float(rule.min_kilometers),
                    'prix_jour_per_km': float(rule.prix_jour_per_km),
                    'prix_nuit_per_km': float(rule.prix_nuit_per_km)
                })
            
            zones_data.append({
                'id': zone.id,
                'name': zone.name,
                'prix_jour': float(zone.prix_jour),
                'prix_nuit': float(zone.prix_nuit),
                'kilometer_rules': km_rules
            })
        
        return Response({
            'success': True,
            'total': len(zones_data),
            'zones': zones_data
        })
        
    except Exception as e:
        logger.error(f"Erreur liste zones VIP: {str(e)}")
        return Response(
            {'error': 'Erreur lors de la récupération'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============= DEMO/TEST ENDPOINTS =============

@extend_schema(
    tags=['Demo'],
    summary='DEMO - Créer une commande directe avec un chauffeur',
    description='API de test pour créer une commande directement assignée à un chauffeur (pour tester WebSocket)'
)
@api_view(['POST'])
def demo_create_direct_order(request):
    """DEMO: Crée une commande directement avec un chauffeur spécifique"""
    customer = get_customer_from_token(request)
    if not customer:
        return Response(
            {'error': 'Authentification requise en tant que client'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Récupérer le driver_id depuis la requête
    driver_id = request.data.get('driver_id')
    if not driver_id:
        return Response(
            {'error': 'driver_id est requis pour cette API de test'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        driver = UserDriver.objects.get(id=driver_id)
        
        # Vérifier que le chauffeur est en ligne
        driver_status, created = DriverStatus.objects.get_or_create(
            driver=driver,
            defaults={'status': 'ONLINE'}
        )
        
        if driver_status.status == 'OFFLINE':
            driver_status.status = 'ONLINE'
            driver_status.save()
            logger.info(f"🔧 DEMO: Chauffeur {driver_id} mis en ligne automatiquement")
        
        # Créer la commande avec les données de test
        order_data = {
            'pickup_address': request.data.get('pickup_address', 'Rue 1.590'),
            'pickup_latitude': request.data.get('pickup_latitude', 3.8968711),
            'pickup_longitude': request.data.get('pickup_longitude', 11.5470538),
            'destination_address': request.data.get('destination_address', 'Awae'),
            'destination_latitude': request.data.get('destination_latitude', 3.83599),
            'destination_longitude': request.data.get('destination_longitude', 11.5505661),
            'vehicle_type_id': request.data.get('vehicle_type_id', 1),
            'city_id': request.data.get('city_id', 1),
            'customer_notes': request.data.get('customer_notes', 'Commande de test WebSocket')
        }
        
        with transaction.atomic():
            order_service = OrderService()
            
            # Créer la commande
            order = order_service.create_order(
                customer_id=customer.id,
                order_data=order_data
            )
            
            # Assigner directement le chauffeur
            order.driver = driver
            order.status = 'ACCEPTED'
            order.accepted_at = timezone.now()
            order.save()
            
            # Mettre le chauffeur en BUSY
            driver_status.status = 'BUSY'
            driver_status.save()
            
            # Créer une entrée dans le pool pour la traçabilité
            DriverPool.objects.create(
                order=order,
                driver=driver,
                priority_order=1,
                distance_km=2.5,  # Distance fictive
                request_status='ACCEPTED',
                requested_at=timezone.now(),
                responded_at=timezone.now(),
                timeout_at=timezone.now()
            )
            
            # Créer l'événement de tracking
            OrderTracking.objects.create(
                order=order,
                event_type='DRIVER_ACCEPTED',
                driver=driver,
                customer=customer,
                notes='Commande de test - Assignation directe',
                metadata={'demo': True, 'driver_id': driver_id}
            )
            
            logger.info(f"✅ DEMO: Commande {order.id} créée et assignée au chauffeur {driver_id}")
            
            # Envoyer notification WebSocket au chauffeur (même pour les commandes DEMO)
            pool_entries = DriverPool.objects.filter(order=order)
            notifications_sent = notify_drivers_new_order(order, pool_entries)
            logger.info(f"🔔 DEMO: Commande {order.id}: {notifications_sent} notification WebSocket envoyée")
            
            return Response({
                'success': True,
                'message': f'Commande de test créée et assignée au chauffeur {driver.name} {driver.surname}',
                'order': OrderSerializer(order).data,
                'driver_info': {
                    'id': driver.id,
                    'name': f"{driver.name} {driver.surname}",
                    'phone': driver.phone_number,
                    'status': driver_status.status
                },
                'notifications_sent': notifications_sent,
                'note': 'Commande créée en mode DEMO - Notification WebSocket envoyée au chauffeur'
            }, status=status.HTTP_201_CREATED)
            
    except UserDriver.DoesNotExist:
        return Response(
            {'error': f'Chauffeur avec ID {driver_id} non trouvé'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Erreur demo create order: {str(e)}")
        return Response(
            {'error': f'Erreur lors de la création: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ============= DEBUG ENDPOINTS =============

@extend_schema(
    tags=['Debug'],
    summary='Debug - État des chauffeurs en ligne',
    description='API de débogage pour vérifier l\'état des chauffeurs ONLINE avec leurs positions'
)
@api_view(['GET'])
def debug_online_drivers(request):
    """Debug : Affiche l'état de tous les chauffeurs ONLINE"""
    try:
        # Récupérer tous les chauffeurs ONLINE
        online_drivers = DriverStatus.objects.filter(
            status='ONLINE'
        ).select_related('driver')
        
        debug_data = {
            'total_online_drivers': online_drivers.count(),
            'drivers': []
        }
        
        for driver_status in online_drivers:
            # Vérifier les véhicules
            vehicles = Vehicle.objects.filter(
                driver=driver_status.driver,
                is_active=True
            )
            
            vehicles_data = []
            for vehicle in vehicles:
                vehicles_data.append({
                    'id': vehicle.id,
                    'nom': vehicle.nom,
                    'is_active': vehicle.is_active,
                    'is_online': vehicle.is_online,
                    'vehicle_type': vehicle.vehicle_type.name if vehicle.vehicle_type else None,
                    'plaque': vehicle.plaque_immatriculation
                })
            
            driver_data = {
                'driver_id': driver_status.driver.id,
                'driver_name': f"{driver_status.driver.name} {driver_status.driver.surname}",
                'status': driver_status.status,
                'has_position': {
                    'latitude': driver_status.current_latitude is not None,
                    'longitude': driver_status.current_longitude is not None,
                    'lat_value': float(driver_status.current_latitude) if driver_status.current_latitude else None,
                    'lng_value': float(driver_status.current_longitude) if driver_status.current_longitude else None
                },
                'last_location_update': driver_status.last_location_update.isoformat() if driver_status.last_location_update else None,
                'session_started_at': driver_status.session_started_at.isoformat() if driver_status.session_started_at else None,
                'total_vehicles': vehicles.count(),
                'active_vehicles': vehicles.filter(is_active=True).count(),
                'online_vehicles': vehicles.filter(is_active=True, is_online=True).count(),
                'vehicles': vehicles_data
            }
            
            debug_data['drivers'].append(driver_data)
        
        return Response({
            'success': True,
            'debug_info': debug_data,
            'message': f'Trouvé {debug_data["total_online_drivers"]} chauffeur(s) ONLINE'
        })
        
    except Exception as e:
        logger.error(f"Erreur debug drivers: {str(e)}")
        return Response(
            {'error': f'Erreur debug: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['Debug'],
    summary='Debug - Test recherche chauffeur avec logs',
    description='API de débogage pour tester la recherche avec logs détaillés'
)
@api_view(['POST'])
def debug_search_drivers(request):
    """Debug : Test la recherche avec logs détaillés"""
    try:
        pickup_lat = float(request.data.get('pickup_latitude', 0))
        pickup_lng = float(request.data.get('pickup_longitude', 0))
        radius_km = float(request.data.get('radius_km', 10))
        vehicle_type_id = request.data.get('vehicle_type_id')
        
        logger.info(f"🔍 DEBUG SEARCH - Pickup: {pickup_lat}, {pickup_lng}")
        logger.info(f"🔍 DEBUG SEARCH - Radius: {radius_km}km")
        logger.info(f"🔍 DEBUG SEARCH - Vehicle type: {vehicle_type_id}")
        
        # Étape 1: Récupérer les chauffeurs ONLINE
        query = DriverStatus.objects.filter(
            status='ONLINE',
            current_latitude__isnull=False,
            current_longitude__isnull=False
        ).select_related('driver')
        
        online_count = query.count()
        logger.info(f"🔍 DEBUG SEARCH - Chauffeurs ONLINE avec position: {online_count}")
        
        debug_steps = {
            'step_1_online_drivers': online_count,
            'step_2_within_radius': 0,
            'step_3_with_vehicles': 0,
            'drivers_details': [],
            'distances_calculated': []
        }
        
        # Étape 2: Calculer les distances
        order_service = OrderService()
        
        for driver_status in query:
            driver_lat = float(driver_status.current_latitude)
            driver_lng = float(driver_status.current_longitude)
            
            distance = order_service.calculate_real_distance(
                pickup_lat, pickup_lng, driver_lat, driver_lng
            )
            
            debug_steps['distances_calculated'].append({
                'driver_id': driver_status.driver.id,
                'driver_name': f"{driver_status.driver.name} {driver_status.driver.surname}",
                'driver_position': [driver_lat, driver_lng],
                'distance_km': round(distance, 2),
                'within_radius': distance <= radius_km
            })
            
            if distance <= radius_km:
                debug_steps['step_2_within_radius'] += 1
                
                # Étape 3: Vérifier les véhicules
                if vehicle_type_id:
                    vehicle = Vehicle.objects.filter(
                        driver=driver_status.driver,
                        vehicle_type_id=vehicle_type_id,
                        is_active=True,
                        is_online=True
                    ).first()
                else:
                    vehicle = Vehicle.objects.filter(
                        driver=driver_status.driver,
                        is_active=True,
                        is_online=True
                    ).first()
                
                if vehicle:
                    debug_steps['step_3_with_vehicles'] += 1
                
                debug_steps['drivers_details'].append({
                    'driver_id': driver_status.driver.id,
                    'distance_km': round(distance, 2),
                    'has_vehicle': vehicle is not None,
                    'vehicle_info': {
                        'id': vehicle.id if vehicle else None,
                        'type': vehicle.vehicle_type.name if vehicle and vehicle.vehicle_type else None,
                        'is_active': vehicle.is_active if vehicle else None,
                        'is_online': vehicle.is_online if vehicle else None
                    } if vehicle else None
                })
        
        logger.info(f"🔍 DEBUG SEARCH - Dans le rayon: {debug_steps['step_2_within_radius']}")
        logger.info(f"🔍 DEBUG SEARCH - Avec véhicules: {debug_steps['step_3_with_vehicles']}")
        
        return Response({
            'success': True,
            'debug_steps': debug_steps,
            'final_result': f"{debug_steps['step_3_with_vehicles']} chauffeur(s) éligible(s)"
        })
        
    except Exception as e:
        logger.error(f"Erreur debug search: {str(e)}")
        return Response(
            {'error': f'Erreur debug: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============= HELPER FUNCTIONS FOR GPS BROADCASTING =============

def _start_driver_location_broadcasting(driver_id):
    """
    Démarrer la diffusion GPS automatique pour un chauffeur
    """
    try:
        channel_layer = get_channel_layer()
        driver_group_name = f'driver_{driver_id}'
        
        # Envoyer un message au consumer pour démarrer la diffusion
        async_to_sync(channel_layer.group_send)(
            driver_group_name,
            {
                'type': 'start_location_broadcasting',
                'driver_id': driver_id
            }
        )
        logger.info(f"🚀📡 DIFFUSION GPS DÉMARRÉE pour le chauffeur {driver_id}")
        logger.info(f"📡 Le chauffeur {driver_id} va diffuser sa position GPS toutes les 5 secondes")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du démarrage de la diffusion GPS pour le chauffeur {driver_id}: {str(e)}")


def _stop_driver_location_broadcasting(driver_id):
    """
    Arrêter la diffusion GPS automatique pour un chauffeur
    """
    try:
        channel_layer = get_channel_layer()
        driver_group_name = f'driver_{driver_id}'
        
        # Envoyer un message au consumer pour arrêter la diffusion
        async_to_sync(channel_layer.group_send)(
            driver_group_name,
            {
                'type': 'stop_location_broadcasting',
                'driver_id': driver_id
            }
        )
        logger.info(f"📡 Diffusion GPS arrêtée pour le chauffeur {driver_id}")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'arrêt de la diffusion GPS pour le chauffeur {driver_id}: {str(e)}")


def _broadcast_driver_location(driver_id, latitude, longitude):
    """
    Diffuser la position d'un chauffeur vers tous les clients connectés qui l'écoutent
    """
    try:
        channel_layer = get_channel_layer()
        
        # Diffuser vers le groupe des clients qui suivent ce chauffeur
        async_to_sync(channel_layer.group_send)(
            f'driver_tracking_{driver_id}',
            {
                'type': 'driver_location_update',
                'driver_id': driver_id,
                'latitude': latitude,
                'longitude': longitude,
                'timestamp': timezone.now().isoformat()
            }
        )
        
        # Également informer le chauffeur lui-même de sa position
        async_to_sync(channel_layer.group_send)(
            f'driver_{driver_id}',
            {
                'type': 'location_broadcast_confirmation',
                'latitude': latitude,
                'longitude': longitude,
                'timestamp': timezone.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la diffusion de la position du chauffeur {driver_id}: {str(e)}")
