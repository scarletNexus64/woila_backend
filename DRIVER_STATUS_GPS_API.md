# 🚗 API Statut Chauffeur & Diffusion GPS

## 📋 Vue d'ensemble

Cette documentation détaille le système de gestion du statut chauffeur (ONLINE/OFFLINE) et la diffusion GPS en temps réel via WebSocket.

## 🔧 Prérequis

**Pour passer ONLINE, un chauffeur DOIT avoir :**
- Au moins 1 véhicule avec `is_active=True` (approuvé par admin)
- Ce véhicule doit être `is_online=True` (en service)

## 🌐 APIs REST - Gestion Statut

### 1. Toggle Status (Recommandé)
```http
POST /order/driver/status/toggle/
Authorization: Bearer {driver_token}
```

**Réponse Succès :**
```json
{
    "success": true,
    "message": "Vous êtes maintenant en ligne",
    "status": "ONLINE",
    "data": {
        "id": 1,
        "driver": 28,
        "status": "ONLINE",
        "current_latitude": "3.84800000",
        "current_longitude": "11.50210000",
        "last_online": "2024-01-15T10:30:00Z"
    }
}
```

**Erreur Véhicule :**
```json
{
    "success": false,
    "error": "Vous devez avoir au moins un véhicule actif et en service pour passer en ligne"
}
```

### 2. Forcer ONLINE
```http
POST /order/driver/status/online/
Authorization: Bearer {driver_token}
```

### 3. Forcer OFFLINE  
```http
POST /order/driver/status/offline/
Authorization: Bearer {driver_token}
```

### 4. Consulter Statut
```http
GET /order/driver/status/
Authorization: Bearer {driver_token}
```

## 📍 API GPS - Mise à jour Position

```http
POST /order/driver/location/update/
Authorization: Bearer {driver_token}
Content-Type: application/json

{
    "latitude": 3.8480,
    "longitude": 11.5021
}
```

**Réponse :**
```json
{
    "success": true,
    "message": "Position mise à jour avec succès",
    "location": {
        "latitude": "3.84800000",
        "longitude": "11.50210000",
        "updated_at": "2024-01-15T10:35:00Z"
    }
}
```

## 🔌 WebSocket - Diffusion GPS Temps Réel

### Connexion Driver
```javascript
const driverSocket = new WebSocket(
    `ws://localhost:8000/ws/driver/${driver_id}/?token=${driver_token}`
);
```

### Messages reçus par le chauffeur

#### Confirmation passage ONLINE
```json
{
    "type": "status_update",
    "status": "ONLINE", 
    "message": "Vous êtes maintenant en ligne"
}
```

#### Démarrage diffusion GPS
```json
{
    "type": "location_broadcasting_started",
    "message": "Diffusion GPS démarrée - Position diffusée toutes les 5 secondes"
}
```

#### Confirmation diffusion (toutes les 5s)
```json
{
    "type": "location_broadcast_confirmation",
    "latitude": 3.8480,
    "longitude": 11.5021,
    "timestamp": "2024-01-15T10:35:00Z",
    "message": "Position diffusée #1"
}
```

### Messages envoyés par le chauffeur

#### Mise à jour position GPS
```json
{
    "type": "location_update",
    "latitude": 3.8480,
    "longitude": 11.5021
}
```

## 📱 WebSocket - Tracking GPS pour Clients

### Connexion Customer (pour suivre un chauffeur)
```javascript
const trackingSocket = new WebSocket(
    `ws://localhost:8000/ws/customer/${customer_id}/?token=${customer_token}`
);
```

### Messages reçus par le client

#### Position chauffeur (toutes les 5s)
```json
{
    "type": "driver_location",
    "driver_id": "28",
    "latitude": 3.8480,
    "longitude": 11.5021,
    "timestamp": "2024-01-15T10:35:00Z"
}
```

## 🔄 Flux Complet d'Intégration

### 1. **Passage ONLINE**
```javascript
// 1. Vérifier statut véhicule d'abord (optionnel)
fetch('/api/vehicles/by-driver/' + driverId, {
    headers: { 'Authorization': 'Bearer ' + token }
})

// 2. Passer ONLINE
fetch('/order/driver/status/toggle/', {
    method: 'POST',
    headers: { 'Authorization': 'Bearer ' + token }
})
.then(response => {
    if (response.ok) {
        // 3. Connecter WebSocket
        connectDriverWebSocket();
        // 4. Démarrer envoi GPS périodique
        startGPSUpdates();
    }
})
```

### 2. **Connexion WebSocket & GPS**
```javascript
function connectDriverWebSocket() {
    const socket = new WebSocket(`ws://localhost:8000/ws/driver/${driverId}/?token=${token}`);
    
    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        switch(data.type) {
            case 'location_broadcasting_started':
                console.log('✅ Diffusion GPS activée');
                break;
                
            case 'location_broadcast_confirmation':
                console.log(`📍 Position diffusée: ${data.latitude}, ${data.longitude}`);
                break;
                
            case 'order_request':
                handleNewOrderRequest(data.order_data);
                break;
        }
    };
}

function startGPSUpdates() {
    // Option A: Via API REST (recommandé)
    setInterval(() => {
        navigator.geolocation.getCurrentPosition((position) => {
            fetch('/order/driver/location/update/', {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer ' + token,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude
                })
            });
        });
    }, 10000); // Toutes les 10s

    // Option B: Via WebSocket
    // socket.send(JSON.stringify({
    //     type: 'location_update',
    //     latitude: lat,
    //     longitude: lng
    // }));
}
```

### 3. **Passage OFFLINE**
```javascript
// 1. Passer OFFLINE
fetch('/order/driver/status/toggle/', {
    method: 'POST',
    headers: { 'Authorization': 'Bearer ' + token }
})

// 2. Fermer WebSocket (arrête auto la diffusion GPS)
socket.close();

// 3. Arrêter envoi GPS
clearInterval(gpsUpdateInterval);
```

## 📊 États & Transitions

| État Initial | Action | État Final | GPS Diffusion |
|--------------|--------|------------|---------------|
| OFFLINE | Toggle/Online | ONLINE | ✅ Démarrée |
| ONLINE | Toggle/Offline | OFFLINE | ❌ Arrêtée |
| ONLINE | Accept Order | BUSY | ✅ Continue |
| BUSY | Complete Order | ONLINE | ✅ Continue |

## ⚠️ Gestion d'Erreurs

### Erreur Véhicule
```json
{
    "success": false,
    "error": "Vous devez avoir au moins un véhicule actif et en service pour passer en ligne"
}
```

**Solution Front :**
```javascript
if (!response.success && response.error.includes('véhicule')) {
    // Rediriger vers page gestion véhicules
    redirectTo('/vehicles/manage');
    showAlert('Veuillez activer un véhicule avant de passer en ligne');
}
```

### Erreur Token
```json
{
    "error": "Authentification requise en tant que chauffeur"
}
```

### Erreur WebSocket
```javascript
socket.onerror = (error) => {
    console.error('WebSocket error:', error);
    // Retry connexion
    setTimeout(connectDriverWebSocket, 5000);
};
```

## 🧪 Tests d'Intégration

### Test avec cURL
```bash
# 1. Test passage online (avec véhicule valide)
curl -X POST http://localhost:8000/order/driver/status/toggle/ \
  -H "Authorization: Bearer YOUR_DRIVER_TOKEN"

# 2. Test mise à jour GPS
curl -X POST http://localhost:8000/order/driver/location/update/ \
  -H "Authorization: Bearer YOUR_DRIVER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"latitude": 3.8480, "longitude": 11.5021}'

# 3. Test passage offline
curl -X POST http://localhost:8000/order/driver/status/toggle/ \
  -H "Authorization: Bearer YOUR_DRIVER_TOKEN"
```

### Test WebSocket (JavaScript)
```javascript
// Test tracking chauffeur depuis client
const trackingSocket = new WebSocket(
    `ws://localhost:8000/ws/customer/${customer_id}/?token=${customer_token}`
);

trackingSocket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'driver_location') {
        console.log(`📍 Chauffeur ${data.driver_id}: ${data.latitude}, ${data.longitude}`);
        // Mettre à jour carte en temps réel
        updateMapMarker(data.driver_id, data.latitude, data.longitude);
    }
};
```

## 🔗 URLs Importantes

- **Driver Status:** `/order/driver/status/`
- **GPS Update:** `/order/driver/location/update/`  
- **WebSocket Driver:** `/ws/driver/{driver_id}/`
- **WebSocket Customer:** `/ws/customer/{customer_id}/`
- **Véhicules Driver:** `/api/vehicles/by-driver/{driver_id}/`

## 💡 Bonnes Pratiques

1. **Toujours vérifier** le statut véhicule avant passage online
2. **Gérer les reconnexions** WebSocket automatiquement
3. **Envoyer GPS** même hors connexion WebSocket (via API REST)
4. **Monitorer** les confirmations de diffusion GPS
5. **Gérer proprement** la fermeture WebSocket au passage offline