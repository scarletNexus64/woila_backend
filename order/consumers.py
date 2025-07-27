import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from api.models import UserDriver, UserCustomer
from .models import DriverStatus, Order, OrderTracking
from .services import OrderService, PricingService


class DriverConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.driver_id = self.scope['url_route']['kwargs']['driver_id']
        self.driver_group_name = f'driver_{self.driver_id}'
        
        # Vérifier que le driver existe
        driver = await self.get_driver(self.driver_id)
        if not driver:
            await self.close()
            return
        
        # Ajouter au groupe des drivers
        await self.channel_layer.group_add(
            self.driver_group_name,
            self.channel_name
        )
        
        # Marquer le driver comme ONLINE
        await self.set_driver_online()
        
        await self.accept()
        
        # Notifier que le driver est en ligne
        await self.send(text_data=json.dumps({
            'type': 'status_update',
            'status': 'ONLINE',
            'message': 'Vous êtes maintenant en ligne'
        }))

    async def disconnect(self, close_code):
        # Marquer le driver comme OFFLINE
        await self.set_driver_offline()
        
        # Quitter le groupe
        await self.channel_layer.group_discard(
            self.driver_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'location_update':
            await self.handle_location_update(data)
        elif message_type == 'accept_order':
            await self.handle_accept_order(data)
        elif message_type == 'start_trip':
            await self.handle_start_trip(data)
        elif message_type == 'complete_trip':
            await self.handle_complete_trip(data)
        elif message_type == 'reject_order':
            await self.handle_reject_order(data)

    async def handle_location_update(self, data):
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if latitude and longitude:
            await self.update_driver_location(latitude, longitude)

    async def handle_accept_order(self, data):
        order_id = data.get('order_id')
        if order_id:
            success = await self.accept_order(order_id)
            if success:
                await self.send(text_data=json.dumps({
                    'type': 'order_accepted',
                    'order_id': order_id,
                    'message': 'Commande acceptée avec succès'
                }))

    async def handle_start_trip(self, data):
        order_id = data.get('order_id')
        if order_id:
            success = await self.start_trip(order_id)
            if success:
                await self.send(text_data=json.dumps({
                    'type': 'trip_started',
                    'order_id': order_id,
                    'message': 'Course démarrée'
                }))

    async def handle_complete_trip(self, data):
        order_id = data.get('order_id')
        if order_id:
            success = await self.complete_trip(order_id)
            if success:
                await self.send(text_data=json.dumps({
                    'type': 'trip_completed',
                    'order_id': order_id,
                    'message': 'Course terminée'
                }))

    async def handle_reject_order(self, data):
        order_id = data.get('order_id')
        if order_id:
            await self.reject_order(order_id)

    # Messages reçus du groupe
    async def order_request(self, event):
        await self.send(text_data=json.dumps({
            'type': 'order_request',
            'order_data': event['order_data']
        }))

    async def order_cancelled(self, event):
        await self.send(text_data=json.dumps({
            'type': 'order_cancelled',
            'order_id': event['order_id'],
            'message': 'Commande annulée par le client'
        }))

    # Méthodes de base de données
    @database_sync_to_async
    def get_driver(self, driver_id):
        try:
            return UserDriver.objects.get(id=driver_id)
        except UserDriver.DoesNotExist:
            return None

    @database_sync_to_async
    def set_driver_online(self):
        driver_status, created = DriverStatus.objects.get_or_create(
            driver_id=self.driver_id,
            defaults={'status': 'ONLINE', 'websocket_channel': self.channel_name}
        )
        if not created:
            driver_status.status = 'ONLINE'
            driver_status.websocket_channel = self.channel_name
            driver_status.last_online = timezone.now()
            driver_status.save()

    @database_sync_to_async
    def set_driver_offline(self):
        try:
            driver_status = DriverStatus.objects.get(driver_id=self.driver_id)
            driver_status.status = 'OFFLINE'
            driver_status.websocket_channel = None
            driver_status.save()
        except DriverStatus.DoesNotExist:
            pass

    @database_sync_to_async
    def update_driver_location(self, latitude, longitude):
        try:
            driver_status = DriverStatus.objects.get(driver_id=self.driver_id)
            driver_status.current_latitude = latitude
            driver_status.current_longitude = longitude
            driver_status.last_location_update = timezone.now()
            driver_status.save()
        except DriverStatus.DoesNotExist:
            pass

    @database_sync_to_async
    def accept_order(self, order_id):
        try:
            order = Order.objects.get(id=order_id, status='PENDING')
            order.driver_id = self.driver_id
            order.status = 'ACCEPTED'
            order.accepted_at = timezone.now()
            order.save()
            
            # Marquer le driver comme occupé
            driver_status = DriverStatus.objects.get(driver_id=self.driver_id)
            driver_status.status = 'BUSY'
            driver_status.save()
            
            # Créer un événement de tracking
            OrderTracking.objects.create(
                order=order,
                event_type='DRIVER_ASSIGNED',
                metadata={'driver_id': self.driver_id}
            )
            
            return True
        except (Order.DoesNotExist, DriverStatus.DoesNotExist):
            return False

    @database_sync_to_async
    def start_trip(self, order_id):
        try:
            order = Order.objects.get(id=order_id, driver_id=self.driver_id, status='ACCEPTED')
            order.status = 'IN_PROGRESS'
            order.started_at = timezone.now()
            order.save()
            
            OrderTracking.objects.create(
                order=order,
                event_type='TRIP_STARTED'
            )
            
            return True
        except Order.DoesNotExist:
            return False

    @database_sync_to_async
    def complete_trip(self, order_id):
        try:
            order = Order.objects.get(id=order_id, driver_id=self.driver_id, status='IN_PROGRESS')
            order.status = 'COMPLETED'
            order.completed_at = timezone.now()
            order.save()
            
            # Libérer le driver
            driver_status = DriverStatus.objects.get(driver_id=self.driver_id)
            driver_status.status = 'ONLINE'
            driver_status.save()
            
            OrderTracking.objects.create(
                order=order,
                event_type='TRIP_COMPLETED'
            )
            
            return True
        except (Order.DoesNotExist, DriverStatus.DoesNotExist):
            return False

    @database_sync_to_async
    def reject_order(self, order_id):
        # La logique de rejet sera implémentée plus tard
        # (rechercher un autre driver disponible)
        pass


class CustomerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.customer_id = self.scope['url_route']['kwargs']['customer_id']
        self.customer_group_name = f'customer_{self.customer_id}'
        
        # Vérifier que le client existe
        customer = await self.get_customer(self.customer_id)
        if not customer:
            await self.close()
            return
        
        # Ajouter au groupe des clients
        await self.channel_layer.group_add(
            self.customer_group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        # Quitter le groupe
        await self.channel_layer.group_discard(
            self.customer_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'create_order':
            await self.handle_create_order(data)
        elif message_type == 'cancel_order':
            await self.handle_cancel_order(data)

    async def handle_create_order(self, data):
        # Créer la commande
        order_data = await self.create_order(data)
        if order_data:
            # Chercher des drivers disponibles
            available_drivers = await self.find_available_drivers()
            
            if available_drivers:
                # Envoyer la demande aux drivers
                for driver_id in available_drivers:
                    await self.channel_layer.group_send(
                        f'driver_{driver_id}',
                        {
                            'type': 'order_request',
                            'order_data': order_data
                        }
                    )
                
                await self.send(text_data=json.dumps({
                    'type': 'order_created',
                    'order_id': order_data['id'],
                    'message': f'Commande créée. Recherche de {len(available_drivers)} chauffeurs...'
                }))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'no_drivers',
                    'message': 'Aucun chauffeur disponible pour le moment'
                }))

    async def handle_cancel_order(self, data):
        order_id = data.get('order_id')
        if order_id:
            success = await self.cancel_order(order_id)
            if success:
                await self.send(text_data=json.dumps({
                    'type': 'order_cancelled',
                    'order_id': order_id,
                    'message': 'Commande annulée'
                }))

    # Messages reçus du groupe
    async def order_accepted(self, event):
        await self.send(text_data=json.dumps({
            'type': 'order_accepted',
            'order_id': event['order_id'],
            'driver_info': event['driver_info'],
            'message': 'Votre commande a été acceptée!'
        }))

    async def trip_started(self, event):
        await self.send(text_data=json.dumps({
            'type': 'trip_started',
            'order_id': event['order_id'],
            'message': 'Votre course a commencé'
        }))

    async def trip_completed(self, event):
        await self.send(text_data=json.dumps({
            'type': 'trip_completed',
            'order_id': event['order_id'],
            'message': 'Course terminée'
        }))

    async def driver_location_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'driver_location',
            'order_id': event['order_id'],
            'latitude': event['latitude'],
            'longitude': event['longitude']
        }))

    # Méthodes de base de données
    @database_sync_to_async
    def get_customer(self, customer_id):
        try:
            return UserCustomer.objects.get(id=customer_id)
        except UserCustomer.DoesNotExist:
            return None

    @database_sync_to_async
    def create_order(self, data):
        try:
            # Calculer le prix avec le service de pricing
            pricing_service = PricingService()
            price_data = pricing_service.calculate_order_price(
                vehicle_type_id=data['vehicle_type_id'],
                city_id=data['city_id'],
                distance_km=data['distance_km'],
                vip_zone_id=data.get('vip_zone_id'),
                is_night=data.get('is_night', False)
            )
            
            order = Order.objects.create(
                customer_id=self.customer_id,
                pickup_address=data['pickup_address'],
                pickup_latitude=data['pickup_latitude'],
                pickup_longitude=data['pickup_longitude'],
                destination_address=data['destination_address'],
                destination_latitude=data['destination_latitude'],
                destination_longitude=data['destination_longitude'],
                vehicle_type_id=data['vehicle_type_id'],
                city_id=data['city_id'],
                vip_zone_id=data.get('vip_zone_id'),
                estimated_distance_km=data['distance_km'],
                customer_notes=data.get('notes', ''),
                **price_data
            )
            
            # Créer un événement de tracking
            OrderTracking.objects.create(
                order=order,
                event_type='ORDER_CREATED'
            )
            
            return {
                'id': str(order.id),
                'pickup_address': order.pickup_address,
                'destination_address': order.destination_address,
                'total_price': float(order.total_price),
                'vehicle_type': order.vehicle_type.name,
                'estimated_distance_km': float(order.estimated_distance_km)
            }
        except Exception as e:
            return None

    @database_sync_to_async
    def find_available_drivers(self):
        # Trouver les drivers en ligne dans la zone
        online_drivers = DriverStatus.objects.filter(
            status='ONLINE',
            current_latitude__isnull=False,
            current_longitude__isnull=False
        ).values_list('driver_id', flat=True)
        
        return list(online_drivers)

    @database_sync_to_async
    def cancel_order(self, order_id):
        try:
            order = Order.objects.get(id=order_id, customer_id=self.customer_id, status='PENDING')
            order.status = 'CANCELLED'
            order.cancelled_at = timezone.now()
            order.save()
            
            OrderTracking.objects.create(
                order=order,
                event_type='ORDER_CANCELLED'
            )
            
            return True
        except Order.DoesNotExist:
            return False