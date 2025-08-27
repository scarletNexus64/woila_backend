# Debug WebSocket Notifications Chauffeur

## Problème Initial
Le chauffeur ne recevait pas les notifications de nouvelles commandes via WebSocket. Le backend envoyait bien les notifications mais l'AlertDialog ne s'affichait pas côté chauffeur Flutter.

## Configuration WebSocket
- **Django API**: Port 8001 (`python3 runserver 8001`)
- **Daphne WebSocket**: Port 8002 (`daphne -p 8002 ...`)
- **URL WebSocket**: `ws://192.168.0.102:8002/ws/driver/{driver_id}/?token={token}`

## Architecture de la Notification

### Backend (Python Django)
1. **Création de commande** dans `views.py` :
   ```python
   notifications_sent = notify_drivers_new_order(order, pool_entries)
   ```

2. **Envoi via group_send** :
   ```python
   async_to_sync(channel_layer.group_send)(
       driver_group_name,  # 'driver_28'
       {
           'type': 'order_request',
           'order_data': order_data
       }
   )
   ```

3. **DriverConsumer** doit avoir une méthode `order_request()` pour traiter les group_send.

### Frontend (Flutter)
1. **WebSocketService** reçoit le message via `_handleMessage()`
2. **Case 'order_request'** appelle `_handleOrderRequest()`
3. **_handleOrderRequest()** doit appeler `_showOrderAlertDialog()`

## Solutions Implémentées

### 1. Méthode validateAndFixAuthData manquante
**Problème**: `AuthService.validateAndFixAuthData()` n'existait pas

**Solution**: Ajout dans `auth_service.dart`:
```dart
Future<Map<String, dynamic>?> validateAndFixAuthData() async {
  // Validation token + userData + userType
  // Retourne les données validées pour WebSocket
}
```

### 2. AlertDialog pour notifications
**Problème**: Pas d'interface utilisateur pour les notifications

**Solution**: Ajout dans `websocket_service.dart`:
```dart
void _showOrderAlertDialog(OrderRequest order) {
  Get.dialog(
    AlertDialog(
      title: Text('🚗 Nouvelle Commande'),
      content: // ... infos commande
      actions: [
        TextButton(onPressed: rejectOrder, child: Text('❌ Refuser')),
        ElevatedButton(onPressed: acceptOrder, child: Text('✅ Accepter')),
      ],
    ),
    barrierDismissible: false,
  );
}
```

### 3. Méthode order_request dans DriverConsumer
**Problème**: La méthode `order_request()` manquait ou était dupliquée

**Solution**: Ajout dans `consumers.py`:
```python
async def order_request(self, event):
    """Gère les demandes de commande reçues via group_send"""
    print(f"🔥🔥🔥 ORDER_REQUEST RECU pour chauffeur {self.driver_id}")
    
    order_data = event.get('order_data', {})
    formatted_data = {
        'id': order_data.get('id'),
        'customer_name': order_data.get('customer_name', ''),
        # ... autres champs
    }
    
    await self.send(text_data=json.dumps({
        'type': 'order_request',
        'order_data': formatted_data
    }))
```

## Tests de Debug Implémentés

### 1. Tests de Connexion
Dans `connect()` du DriverConsumer :
```python
# Test direct
await self.send(text_data=json.dumps({
    'type': 'test_direct',
    'message': f'Test DIRECT pour chauffeur {self.driver_id}'
}))

# Test group_send  
await self.channel_layer.group_send(
    self.driver_group_name,
    {'type': 'test_group', 'message': f'Test GROUP pour chauffeur {self.driver_id}'}
)
```

### 2. Cases de Test Flutter
Dans `_handleMessage()` :
```dart
case 'test_direct':
  debugPrint('🧪🧪 TEST DIRECT RECU: ${data['message']}');
  break;
case 'test_group_received':
  debugPrint('🧪🧪 TEST GROUP RECU: ${data['message']}');
  break;
```

### 3. Test Shell Manuel
```python
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

channel_layer = get_channel_layer()
async_to_sync(channel_layer.group_send)(
    'driver_28',
    {
        'type': 'order_request',  
        'order_data': {'id': 'test-456', 'customer_name': 'Test Client'}
    }
)
```

## État Actuel du Debug

### ✅ Ce qui fonctionne :
- Connexion WebSocket chauffeur au port 8002
- Messages directs (`test_direct`)
- Messages groupe (`test_group`)
- Diffusion GPS bidirectionnelle
- Authentification et validation des données

### ❌ Ce qui ne fonctionne pas :
- La méthode `order_request()` n'est jamais appelée côté backend
- Pas de logs `🔥🔥🔥 ORDER_REQUEST RECU` dans Daphne
- Aucun message `order_request` reçu côté Flutter

### Logs Observés :
**Backend Django** : ✅ Envoi notification confirmé
```
📤 Envoi notification WebSocket → Chauffeur 28 (groupe: driver_28)
✅ Notification envoyée au chauffeur 28
```

**Backend Daphne** : ✅ Tests simples fonctionnent, ❌ order_request non reçu

**Frontend Flutter** : ✅ Reçoit tests et GPS, ❌ jamais d'order_request

## Prochaines Étapes de Debug

### 1. Test order_request simplifié
Remplacer la méthode `order_request()` par une version ultra simple :
```python
async def order_request(self, event):
    print(f"🔥🔥🔥 ORDER_REQUEST TEST SIMPLE pour {self.driver_id}")
    await self.send(text_data=json.dumps({
        'type': 'order_request_simple_test',
        'message': f'Test simple pour chauffeur {self.driver_id}'
    }))
```

### 2. Vérifier Django Channels
- Vérifier la configuration `CHANNEL_LAYERS` dans settings.py
- Vérifier que Redis/InMemory backend fonctionne
- Tester avec d'autres types de messages

### 3. Debug Consumer Methods
- Lister toutes les méthodes disponibles dans DriverConsumer
- Vérifier s'il y a des conflits de noms de méthodes
- Vérifier l'héritage de AsyncWebsocketConsumer

## Configuration Technique

### Ports
- Django: `http://192.168.0.102:8001`
- WebSocket: `ws://192.168.0.102:8002`

### URLs de Routing
```python
# routing.py
websocket_urlpatterns = [
    re_path(r'ws/driver/(?P<driver_id>\w+)/$', consumers.DriverConsumer.as_asgi()),
    re_path(r'ws/customer/(?P<customer_id>\w+)/$', consumers.CustomerConsumer.as_asgi()),
]
```

### Flutter WebSocket Service
```dart
// Connection
final wsUrl = '${ApiConstants.wsBaseUrl}/ws/driver/$_driverId/?token=$_authToken';
_channel = WebSocketChannel.connect(wsUrl);
```

## Notes Importantes
- Les tests directs et group_send basiques fonctionnent
- Le problème est spécifique à la méthode `order_request()`
- Possibilité d'exception silencieuse dans le consumer
- WebSocket stable pour autres messages (GPS, status)

## Fichiers Modifiés
1. `auth_service.dart` - Ajout validateAndFixAuthData()
2. `websocket_service.dart` - Ajout _showOrderAlertDialog()
3. `consumers.py` - Ajout order_request() avec debug
4. `api_constants.dart` - Port WebSocket 8002 confirmé