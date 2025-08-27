import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class DriverConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.location_broadcasting_task = None
        
    async def connect(self):
        self.driver_id = self.scope['url_route']['kwargs']['driver_id']
        self.driver_group_name = f'driver_{self.driver_id}'
        
        print(f"🔌 NOUVELLE CONNEXION WebSocket pour chauffeur {self.driver_id}")
        
        # Vérifier que le driver existe
        driver = await self.get_driver(self.driver_id)
        if not driver:
            print(f"❌ Chauffeur {self.driver_id} non trouvé - Connexion refusée")
            await self.close()
            return
        
        print(f"✅ Chauffeur {self.driver_id} trouvé: {driver}")
        
        # Ajouter au groupe des drivers
        await self.channel_layer.group_add(
            self.driver_group_name,
            self.channel_name
        )
        
        print(f"📡 Chauffeur {self.driver_id} ajouté au groupe '{self.driver_group_name}'")
        
        # Marquer le driver comme ONLINE
        await self.set_driver_online()
        
        await self.accept()
        print(f"✅ Connexion WebSocket acceptée pour chauffeur {self.driver_id}")
        
        print(f"🧪 TEST: Envoi message direct au chauffeur {self.driver_id}")
        await self.send(text_data=json.dumps({
            'type': 'test_direct',
            'message': f'Test DIRECT pour chauffeur {self.driver_id}'
        }))

        print(f"🧪 TEST: Envoi via group_send au groupe {self.driver_group_name}")
        await self.channel_layer.group_send(
            self.driver_group_name,
            {
                'type': 'test_group',
                'message': f'Test GROUP pour chauffeur {self.driver_id}'
            }
        )
        
        # Notifier que le driver est en ligne
        await self.send(text_data=json.dumps({
            'type': 'status_update',
            'status': 'ONLINE',
            'message': 'Vous êtes maintenant en ligne'
        }))
        
        print(f"🚀 DÉMARRAGE diffusion GPS automatique pour chauffeur {self.driver_id}")
        # Démarrer automatiquement la diffusion GPS
        await self.start_location_broadcasting({'driver_id': self.driver_id})

    async def disconnect(self, close_code):
        # Arrêter la diffusion GPS
        await self.stop_location_broadcasting({'driver_id': self.driver_id})
        
        # Marquer le driver comme OFFLINE
        await self.set_driver_offline()
        
        # Quitter le groupe
        await self.channel_layer.group_discard(
            self.driver_group_name,
            self.channel_name
        )

    async def test_group(self, event):
        """Test pour group_send"""
        print(f"🧪🧪 TEST_GROUP reçu pour chauffeur {self.driver_id}: {event['message']}")
        await self.send(text_data=json.dumps({
            'type': 'test_group_received',
            'message': event['message']
        }))
        print(f"🧪✅ test_group envoyé au chauffeur {self.driver_id}")

    async def test_direct(self, event):
        """Test pour message direct"""
        print(f"🧪🧪 TEST_DIRECT reçu pour chauffeur {self.driver_id}")
        await self.send(text_data=json.dumps(event))

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
        
        print(f"📱 RÉCEPTION position GPS depuis Flutter: chauffeur {self.driver_id} → ({latitude}, {longitude})")
        
        if latitude and longitude:
            await self.update_driver_location(latitude, longitude)
            print(f"🔄 Position GPS sauvegardée en base de données")
        else:
            print(f"❌ Coordonnées GPS manquantes: latitude={latitude}, longitude={longitude}")

    async def handle_accept_order(self, data):
        order_id = data.get('order_id')
        if order_id:
            print(f"✅ Chauffeur {self.driver_id} accepte commande {order_id}")
            success, order_data = await self.accept_order(order_id)
            if success:
                print(f"✅ Acceptation réussie pour commande {order_id}")
                
                # Confirmer au chauffeur
                await self.send(text_data=json.dumps({
                    'type': 'order_accepted',
                    'order_id': order_id,
                    'message': 'Commande acceptée avec succès'
                }))
                
                # Notifier le client que sa commande a été acceptée
                if order_data:
                    await self.notify_customer_order_accepted(order_data)
            else:
                print(f"❌ Échec acceptation commande {order_id}")
                await self.send(text_data=json.dumps({
                    'type': 'order_acceptance_failed',
                    'order_id': order_id,
                    'message': 'Impossible d\'accepter cette commande'
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
        reason = data.get('reason', 'Chauffeur non disponible')
        if order_id:
            print(f"❌ Chauffeur {self.driver_id} refuse commande {order_id} - Raison: {reason}")
            await self.reject_order(order_id, reason)

    # Messages reçus du groupe
    # Remplacez votre méthode order_request par celle-ci avec plus de logs :

    # async def order_request(self, event):
    #     """
    #     Gère les demandes de commande reçues via group_send
    #     """
    #     print(f"🎯🎯 ORDER_REQUEST RECU dans DriverConsumer pour chauffeur {self.driver_id}")
    #     print(f"🎯 Event reçu: {event}")
        
    #     order_data = event.get('order_data', {})
    #     print(f"📦 Order data: {order_data}")
        
    #     # S'assurer que le format correspond à ce qu'attend l'app Flutter
    #     formatted_data = {
    #         'id': order_data.get('id'),
    #         'order_id': order_data.get('id'),  # Alias pour compatibilité
    #         'customer_id': order_data.get('customer_id', ''),
    #         'customer_name': order_data.get('customer_name', ''),
    #         'customer_phone': order_data.get('customer_phone', ''),
    #         'pickup_address': order_data.get('pickup_address', ''),
    #         'pickup_latitude': order_data.get('pickup_latitude', 0),
    #         'pickup_longitude': order_data.get('pickup_longitude', 0),
    #         'destination_address': order_data.get('destination_address', ''),
    #         'destination_latitude': order_data.get('destination_latitude', 0),
    #         'destination_longitude': order_data.get('destination_longitude', 0),
    #         'estimated_distance_km': order_data.get('estimated_distance_km', 0),
    #         'total_price': order_data.get('total_price', 0),
    #         'vehicle_type': order_data.get('vehicle_type', 'Standard'),
    #         'customer_notes': order_data.get('customer_notes', ''),
    #         'timeout_seconds': order_data.get('timeout_seconds', 30),
    #         'created_at': order_data.get('created_at'),
    #     }
        
    #     message_to_send = {
    #         'type': 'order_request',
    #         'order_data': formatted_data
    #     }
        
    #     print(f"📤 ENVOI MESSAGE AU CHAUFFEUR {self.driver_id}:")
    #     print(f"📤 Message: {json.dumps(message_to_send, indent=2)}")
        
    #     try:
    #         await self.send(text_data=json.dumps(message_to_send))
    #         print(f"✅ Message order_request envoyé avec succès au chauffeur {self.driver_id}")
    #     except Exception as e:
    #         print(f"❌ ERREUR envoi message: {e}")
        
    #     print(f"🎯🎯 FIN order_request pour chauffeur {self.driver_id}")

# Dans votre DriverConsumer, remplacez la méthode order_request par :

    async def order_request(self, event):
        """
        Gère les demandes de commande reçues via group_send
        """
        import logging
        logger = logging.getLogger(__name__)
        
        print("🔥🔥🔥🔥🔥 ORDER_REQUEST METHOD CALLED 🔥🔥🔥🔥🔥")
        logger.error("🔥🔥🔥🔥🔥 ORDER_REQUEST METHOD CALLED 🔥🔥🔥🔥🔥")
        
        print(f"🔥🔥🔥 ORDER_REQUEST APPELÉE pour chauffeur {self.driver_id}")
        print(f"🔥 Event complet: {event}")
        print(f"🔥 Channel name: {self.channel_name}")
        print(f"🔥 Driver group: {self.driver_group_name}")
        
        # Test simple d'abord
        try:
            simple_test = {
                'type': 'order_request_test', 
                'message': f'TEST METHOD WORKS for driver {self.driver_id}'
            }
            await self.send(text_data=json.dumps(simple_test))
            print(f"✅ Simple test message sent to driver {self.driver_id}")
        except Exception as e:
            print(f"❌ ERROR simple test: {e}")
        
        order_data = event.get('order_data', {})
        
        if not order_data:
            print(f"❌ Pas d'order_data dans l'event!")
            # Envoyer quand même un message de test
            test_msg = {'type': 'order_request', 'message': 'NO ORDER DATA'}
            await self.send(text_data=json.dumps(test_msg))
            return
        
        print(f"📦 Order data trouvé: {order_data.get('id')}")
        
        # Message simple pour tester
        simple_message = {
            'type': 'order_request',
            'order_data': {
                'id': order_data.get('id', 'no-id'),
                'customer_name': order_data.get('customer_name', 'Test'),
                'total_price': order_data.get('total_price', 1000)
            }
        }
        
        print(f"📤 Envoi message simple: {simple_message}")
        
        try:
            await self.send(text_data=json.dumps(simple_message))
            print(f"✅ SUCCESS: Message envoyé au chauffeur {self.driver_id}")
        except Exception as e:
            print(f"❌ ERREUR send(): {e}")
            print(f"❌ Type erreur: {type(e)}")
        
        print(f"🔥🔥🔥 FIN order_request pour chauffeur {self.driver_id}")

    async def order_cancelled(self, event):
        await self.send(text_data=json.dumps({
            'type': 'order_cancelled',
            'order_id': event['order_id'],
            'message': 'Commande annulée par le client'
        }))

    # ============= MÉTHODES DE DIFFUSION GPS =============
    
    async def start_location_broadcasting(self, event):
        """
        Démarrer la diffusion automatique de la position GPS toutes les 5 secondes
        """
        print(f"🎯 start_location_broadcasting appelé pour chauffeur {self.driver_id}")
        
        if self.location_broadcasting_task and not self.location_broadcasting_task.done():
            print(f"⚠️ Diffusion GPS déjà en cours pour chauffeur {self.driver_id}")
            return  # Déjà en cours
            
        print(f"🚀 Création de la tâche de diffusion GPS pour chauffeur {self.driver_id}")
        self.location_broadcasting_task = asyncio.create_task(self._location_broadcast_loop())
        
        await self.send(text_data=json.dumps({
            'type': 'location_broadcasting_started',
            'message': 'Diffusion GPS démarrée - Position diffusée toutes les 5 secondes'
        }))
        
        print(f"✅ Diffusion GPS démarrée pour chauffeur {self.driver_id}")

    async def stop_location_broadcasting(self, event):
        """
        Arrêter la diffusion automatique de la position GPS
        """
        if self.location_broadcasting_task and not self.location_broadcasting_task.done():
            self.location_broadcasting_task.cancel()
            
        await self.send(text_data=json.dumps({
            'type': 'location_broadcasting_stopped',
            'message': 'Diffusion GPS arrêtée'
        }))

    async def _location_broadcast_loop(self):
        """
        Boucle de diffusion GPS toutes les 5 secondes
        """
        try:
            loop_count = 0
            print(f"🎯 DÉBUT de la boucle de diffusion GPS pour chauffeur {self.driver_id}")
            
            while True:
                loop_count += 1
                print(f"🔄 GPS Loop #{loop_count} pour chauffeur {self.driver_id}")
                
                try:
                    # Récupérer la position actuelle du chauffeur
                    print(f"📍 Récupération position GPS pour chauffeur {self.driver_id}...")
                    driver_position = await self.get_driver_current_position()
                    print(f"📍 Position récupérée: {driver_position}")
                    
                    if driver_position and driver_position['latitude'] and driver_position['longitude']:
                        # Convertir Decimal en float pour la sérialisation JSON
                        lat = float(driver_position['latitude'])
                        lon = float(driver_position['longitude'])
                        timestamp = timezone.now().isoformat()
                        
                        print(f"📍 DIFFUSION GPS #{loop_count}: Chauffeur {self.driver_id} → ({lat}, {lon}) à {timestamp}")
                        
                        # Diffuser vers les clients qui suivent ce chauffeur
                        await self.channel_layer.group_send(
                            f'driver_tracking_{self.driver_id}',
                            {
                                'type': 'driver_location_update',
                                'driver_id': self.driver_id,
                                'latitude': lat,
                                'longitude': lon,
                                'timestamp': timestamp
                            }
                        )
                        
                        print(f"✅ Position diffusée vers channel 'driver_tracking_{self.driver_id}'")
                        
                        # Confirmation au chauffeur
                        await self.send(text_data=json.dumps({
                            'type': 'location_broadcast_confirmation',
                            'latitude': lat,
                            'longitude': lon,
                            'timestamp': timestamp,
                            'message': f'Position diffusée #{loop_count}'
                        }))
                        
                        print(f"✅ Confirmation envoyée au chauffeur {self.driver_id}")
                    else:
                        print(f"⚠️ Pas de position GPS pour le chauffeur {self.driver_id} (position: {driver_position})")
                    
                    print(f"⏳ Attente 5 secondes avant la prochaine diffusion...")
                    # Attendre 5 secondes
                    await asyncio.sleep(5)
                    
                except Exception as loop_error:
                    print(f"❌ Erreur dans la boucle GPS #{loop_count}: {loop_error}")
                    print(f"🔄 Continuant la boucle malgré l'erreur...")
                    await asyncio.sleep(5)
                
        except asyncio.CancelledError:
            print(f"🛑 Tâche de diffusion GPS annulée pour chauffeur {self.driver_id}")
            pass
        except Exception as e:
            print(f"❌ ERREUR FATALE dans la boucle de diffusion GPS: {e}")
            # Erreur inattendue
            await self.send(text_data=json.dumps({
                'type': 'location_broadcasting_error',
                'message': f'Erreur de diffusion GPS: {str(e)}'
            }))

    async def location_broadcast_confirmation(self, event):
        """
        Recevoir la confirmation de diffusion GPS
        """
        await self.send(text_data=json.dumps({
            'type': 'location_broadcast_confirmation',
            'latitude': event['latitude'],
            'longitude': event['longitude'],
            'timestamp': event['timestamp']
        }))

    # Méthodes de base de données avec imports lazy
    @database_sync_to_async
    def get_driver(self, driver_id):
        try:
            from api.models import UserDriver
            return UserDriver.objects.get(id=driver_id)
        except UserDriver.DoesNotExist:
            return None

    @database_sync_to_async
    def set_driver_online(self):
        from .models import DriverStatus
        driver_status, created = DriverStatus.objects.get_or_create(
            driver_id=self.driver_id,
            defaults={'status': 'ONLINE', 'websocket_channel': self.channel_name}
        )
        if not created:
            driver_status.status = 'ONLINE'
            driver_status.websocket_channel = self.channel_name
            driver_status.last_online = timezone.now()
            driver_status.save()
            
        print(f"📊 Status chauffeur {self.driver_id}: {driver_status.status}")
        if driver_status.current_latitude and driver_status.current_longitude:
            print(f"📍 Position GPS disponible: ({driver_status.current_latitude}, {driver_status.current_longitude})")
        else:
            print(f"⚠️ Pas de position GPS - En attente de mise à jour depuis Flutter")

    @database_sync_to_async
    def set_driver_offline(self):
        try:
            from .models import DriverStatus
            driver_status = DriverStatus.objects.get(driver_id=self.driver_id)
            driver_status.status = 'OFFLINE'
            driver_status.websocket_channel = None
            driver_status.save()
        except DriverStatus.DoesNotExist:
            pass

    @database_sync_to_async
    def update_driver_location(self, latitude, longitude):
        try:
            from .models import DriverStatus
            driver_status = DriverStatus.objects.get(driver_id=self.driver_id)
            driver_status.current_latitude = latitude
            driver_status.current_longitude = longitude
            driver_status.last_location_update = timezone.now()
            driver_status.save()
            print(f"✅ Position GPS mise à jour pour chauffeur {self.driver_id}: ({latitude}, {longitude})")
        except DriverStatus.DoesNotExist:
            print(f"❌ DriverStatus non trouvé pour chauffeur {self.driver_id}")
            pass

    @database_sync_to_async
    def get_driver_current_position(self):
        """
        Récupérer la position GPS actuelle du chauffeur
        """
        try:
            from .models import DriverStatus
            driver_status = DriverStatus.objects.get(driver_id=self.driver_id)
            print(f" DriverStatus pour chauffeur {driver_status}")
            return {
                'latitude': driver_status.current_latitude,
                'longitude': driver_status.current_longitude
            }
        except DriverStatus.DoesNotExist:
            return None

    @database_sync_to_async
    def accept_order(self, order_id):
        try:
            from .models import Order, DriverStatus, OrderTracking
            from api.models import UserDriver
            
            order = Order.objects.get(id=order_id, status='PENDING')
            order.driver_id = self.driver_id
            order.status = 'ACCEPTED'
            order.accepted_at = timezone.now()
            order.save()
            
            # Marquer le driver comme occupé
            driver_status = DriverStatus.objects.get(driver_id=self.driver_id)
            driver_status.status = 'BUSY'
            driver_status.save()
            
            # Récupérer les informations du chauffeur
            driver = UserDriver.objects.get(id=self.driver_id)
            
            # Créer un événement de tracking
            OrderTracking.objects.create(
                order=order,
                event_type='DRIVER_ASSIGNED',
                metadata={'driver_id': self.driver_id}
            )
            
            # Préparer les données de la commande pour le client
            order_data = {
                'order_id': str(order.id),
                'status': order.status,
                'customer_id': order.customer_id,
                'driver_info': {
                    'id': driver.id,
                    'name': f"{driver.name} {driver.surname}",
                    'phone': driver.phone_number,
                    'rating': 4.5,  # TODO: Récupérer la vraie note
                },
                'pickup_address': order.pickup_address,
                'destination_address': order.destination_address,
                'estimated_price': float(order.total_price),
                'accepted_at': order.accepted_at.isoformat(),
            }
            
            return True, order_data
        except Exception as e:
            print(f"❌ Erreur accept_order: {e}")
            return False, None

    @database_sync_to_async
    def start_trip(self, order_id):
        try:
            from .models import Order, OrderTracking
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
            from .models import Order, DriverStatus, OrderTracking
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
        except Exception:
            return False

    @database_sync_to_async
    def reject_order(self, order_id, reason='Chauffeur non disponible'):
        try:
            from .models import Order, DriverPool, OrderTracking
            
            # Trouver l'entrée du pool pour ce chauffeur et cette commande
            pool_entry = DriverPool.objects.filter(
                order_id=order_id,
                driver_id=self.driver_id,
                request_status='PENDING'
            ).first()
            
            if pool_entry:
                pool_entry.request_status = 'REJECTED'
                pool_entry.rejection_reason = reason
                pool_entry.responded_at = timezone.now()
                pool_entry.save()
                
                # Créer un événement de tracking
                OrderTracking.objects.create(
                    order=pool_entry.order,
                    event_type='DRIVER_REJECTED',
                    driver_id=self.driver_id,
                    notes=reason
                )
                
                print(f"❌ Commande {order_id} refusée par chauffeur {self.driver_id}: {reason}")
                return True
            else:
                print(f"⚠️ Pool entry non trouvé pour commande {order_id} et chauffeur {self.driver_id}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur reject_order: {e}")
            return False
    
    async def notify_customer_order_accepted(self, order_data):
        """
        Notifier le client que sa commande a été acceptée par un chauffeur
        """
        try:
            customer_id = order_data['customer_id']
            customer_group_name = f'customer_{customer_id}'
            
            print(f"📤 Envoi notification acceptation → Client {customer_id} (groupe: {customer_group_name})")
            
            # Envoyer la notification au client via WebSocket
            await self.channel_layer.group_send(
                customer_group_name,
                {
                    'type': 'order_accepted',
                    'order_id': order_data['order_id'],
                    'driver_info': order_data['driver_info'],
                    'message': f"Votre commande a été acceptée par {order_data['driver_info']['name']}"
                }
            )
            
            print(f"✅ Notification d'acceptation envoyée au client {customer_id}")
            
        except Exception as e:
            print(f"❌ Erreur notification client: {e}")


class CustomerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Récupérer le customer_id de l'URL
        self.customer_id = self.scope['url_route']['kwargs']['customer_id']
        self.customer_group_name = f'customer_{self.customer_id}'
        
        print(f"🔌 NOUVELLE CONNEXION WebSocket CUSTOMER pour client {self.customer_id}")
        
        # Vérifier l'authentification
        token = None
        if 'query_string' in self.scope:
            query_string = self.scope['query_string'].decode()
            for param in query_string.split('&'):
                if param.startswith('token='):
                    token = param.split('=', 1)[1]
                    break
        
        if not token:
            print(f"❌ Token manquant pour client {self.customer_id}")
            await self.close()
            return
            
        # Vérifier que le client existe et que le token est valide
        customer = await self.get_customer_with_token(self.customer_id, token)
        if not customer:
            print(f"❌ Client {self.customer_id} non trouvé ou token invalide")
            await self.close()
            return
        
        print(f"✅ Client {self.customer_id} authentifié: {customer}")
        
        # Ajouter au groupe des clients
        await self.channel_layer.group_add(
            self.customer_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        print(f"✅ Connexion WebSocket acceptée pour client {self.customer_id}")
        
        print(f"🧪 TEST: Customer connecté - client ID: {self.customer_id}")
        # Notifier que le client est en ligne
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connexion WebSocket établie avec succès',
            'customer_id': self.customer_id
        }))

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
        # Logique de création de commande simplifiée
        await self.send(text_data=json.dumps({
            'type': 'order_created',
            'message': 'Commande créée avec succès'
        }))

    async def handle_cancel_order(self, data):
        order_id = data.get('order_id')
        if order_id:
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
            'driver_info': event.get('driver_info', {}),
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
            'driver_id': event['driver_id'],
            'latitude': event['latitude'],
            'longitude': event['longitude'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def get_customer(self, customer_id):
        try:
            from api.models import UserCustomer
            return UserCustomer.objects.get(id=customer_id)
        except UserCustomer.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_customer_with_token(self, customer_id, token):
        try:
            from api.models import UserCustomer, Token
            
            # Vérifier le token
            token_obj = Token.objects.get(token=token, is_active=True, user_type='customer')
            if str(token_obj.user_id) != str(customer_id):
                print(f"❌ Token user_id mismatch: {token_obj.user_id} != {customer_id}")
                return None
            
            # Récupérer le client
            customer = UserCustomer.objects.get(id=customer_id)
            return customer
        except (Token.DoesNotExist, UserCustomer.DoesNotExist) as e:
            print(f"❌ Erreur authentification customer: {e}")
            return None