# 📚 Documentation API - Module Commande VTC

## 🔐 Authentification
Tous les endpoints nécessitent un token Bearer dans le header :
```
Authorization: Bearer {token}
```

---

## 🚗 DRIVER ENDPOINTS

### 1. Toggle Status (Online/Offline)
**POST** `/api/v1/order/driver/status/toggle/`
```json
// Response
{
    "success": true,
    "message": "Vous êtes maintenant en ligne",
    "status": "ONLINE",
    "data": {
        "id": 1,
        "driver": 1,
        "driver_name": "John Doe",
        "status": "ONLINE",
        "current_latitude": "4.0511",
        "current_longitude": "9.7679"
    }
}
```

### 2. Update Location
**POST** `/api/v1/order/driver/location/update/`
```json
// Request
{
    "latitude": 4.0511,
    "longitude": 9.7679,
    "speed_kmh": 45.5,
    "heading": 180,
    "accuracy": 5.0
}

// Response
{
    "success": true,
    "message": "Position mise à jour",
    "current_location": {
        "latitude": 4.0511,
        "longitude": 9.7679,
        "last_update": "2024-01-15T10:30:00Z"
    }
}
```

### 3. Accept Order
**POST** `/api/v1/order/driver/order/{order_id}/accept/`
```json
// Response
{
    "success": true,
    "message": "Commande acceptée avec succès",
    "order": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "customer_name": "Jane Smith",
        "pickup_address": "Akwa, Douala",
        "destination_address": "Bonanjo, Douala",
        "total_price": "2500.00",
        "status": "ACCEPTED"
    }
}
```

### 4. Reject Order
**POST** `/api/v1/order/driver/order/{order_id}/reject/`
```json
// Request
{
    "reason": "Trop loin de ma position actuelle"
}

// Response
{
    "success": true,
    "message": "Commande refusée"
}
```

### 5. Driver Arrived
**POST** `/api/v1/order/driver/order/{order_id}/arrived/`
```json
// Response
{
    "success": true,
    "message": "Arrivée enregistrée",
    "order": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "status": "DRIVER_ARRIVED"
    }
}
```

### 6. Start Trip
**POST** `/api/v1/order/driver/order/{order_id}/start/`
```json
// Response
{
    "success": true,
    "message": "Course démarrée",
    "order": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "status": "IN_PROGRESS",
        "started_at": "2024-01-15T10:35:00Z"
    }
}
```

### 7. Complete Trip
**POST** `/api/v1/order/driver/order/{order_id}/complete/`
```json
// Request
{
    "actual_distance_km": 8.7,
    "waiting_time": 5,
    "driver_notes": "Client très ponctuel"
}

// Response
{
    "success": true,
    "message": "Course terminée",
    "final_price": 2875.50,
    "order": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "status": "COMPLETED",
        "final_price": "2875.50"
    }
}
```

### 8. Get Current Order
**GET** `/api/v1/order/driver/order/current/`
```json
// Response
{
    "success": true,
    "order": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "customer_name": "Jane Smith",
        "pickup_address": "Akwa, Douala",
        "destination_address": "Bonanjo, Douala",
        "status": "IN_PROGRESS"
    }
}
```

### 9. Get Order History
**GET** `/api/v1/order/driver/order/history/?page=1&page_size=20`
```json
// Response
{
    "success": true,
    "total": 150,
    "page": 1,
    "page_size": 20,
    "orders": [
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "customer_name": "Jane Smith",
            "pickup_address": "Akwa, Douala",
            "destination_address": "Bonanjo, Douala",
            "total_price": "2500.00",
            "status": "COMPLETED",
            "created_at": "2024-01-15T09:00:00Z",
            "driver_rating": 5
        }
    ]
}
```

---

## 👤 CUSTOMER ENDPOINTS

### 1. Search Drivers
**POST** `/api/v1/order/customer/search-drivers/`
```json
// Request
{
    "pickup_latitude": 4.0511,
    "pickup_longitude": 9.7679,
    "vehicle_type_id": 1,
    "radius_km": 5
}

// Response
{
    "success": true,
    "drivers_found": 5,
    "vehicle_types": [
        {
            "type": "Taxi Jaune",
            "count": 3,
            "nearest_distance": 0.5,
            "drivers": [1, 2, 3]
        },
        {
            "type": "Confort",
            "count": 2,
            "nearest_distance": 1.2,
            "drivers": [4, 5]
        }
    ],
    "drivers": [
        {
            "driver_id": 1,
            "driver_name": "John Doe",
            "distance_km": 0.5,
            "latitude": 4.0520,
            "longitude": 9.7680,
            "vehicle": {
                "type": "Taxi Jaune",
                "plaque": "CE-123-AB",
                "brand": "Toyota",
                "model": "Corolla",
                "color": "Jaune"
            },
            "rating": 4.5,
            "orders_today": 8
        }
    ]
}
```

### 2. Estimate Price
**POST** `/api/v1/order/customer/estimate-price/`
```json
// Request
{
    "pickup_latitude": 4.0511,
    "pickup_longitude": 9.7679,
    "destination_latitude": 4.0300,
    "destination_longitude": 9.7100,
    "vehicle_type_id": 1,
    "city_id": 1,
    "vip_zone_id": null
}

// Response
{
    "success": true,
    "distance_km": 8.5,
    "price_estimate": {
        "min_price": "2375.00",
        "max_price": "3100.00",
        "estimated_price": "2737.50",
        "is_night_fare": false,
        "currency": "FCFA"
    }
}
```

### 3. Create Order
**POST** `/api/v1/order/customer/order/create/`
```json
// Request
{
    "pickup_address": "Akwa, Douala",
    "pickup_latitude": 4.0511,
    "pickup_longitude": 9.7679,
    "destination_address": "Bonanjo, Douala",
    "destination_latitude": 4.0300,
    "destination_longitude": 9.7100,
    "vehicle_type_id": 1,
    "city_id": 1,
    "vip_zone_id": null,
    "payment_method_id": 1,
    "customer_notes": "Devant la pharmacie"
}

// Response
{
    "success": true,
    "message": "Commande créée, recherche de chauffeur en cours",
    "order": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "pickup_address": "Akwa, Douala",
        "destination_address": "Bonanjo, Douala",
        "estimated_distance_km": "8.50",
        "total_price": "2625.00",
        "status": "PENDING",
        "payment_method_name": "Espèces"
    },
    "drivers_contacted": 5
}
```

### 4. Cancel Order
**POST** `/api/v1/order/customer/order/{order_id}/cancel/`
```json
// Request
{
    "reason": "Changement de programme"
}

// Response
{
    "success": true,
    "message": "Commande annulée",
    "order": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "status": "CANCELLED",
        "cancellation_reason": "Changement de programme"
    }
}
```

### 5. Track Order
**GET** `/api/v1/order/customer/order/{order_id}/track/`
```json
// Response
{
    "success": true,
    "order": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "driver_name": "John Doe",
        "status": "IN_PROGRESS",
        "pickup_address": "Akwa, Douala",
        "destination_address": "Bonanjo, Douala"
    },
    "driver_location": {
        "latitude": 4.0450,
        "longitude": 9.7500,
        "last_update": "2024-01-15T10:40:00Z"
    },
    "tracking_events": [
        {
            "event_type": "TRIP_STARTED",
            "created_at": "2024-01-15T10:35:00Z"
        },
        {
            "event_type": "DRIVER_ARRIVED",
            "created_at": "2024-01-15T10:30:00Z"
        }
    ]
}
```

### 6. Rate Order
**POST** `/api/v1/order/customer/order/{order_id}/rate/`
```json
// Request
{
    "score": 5,
    "comment": "Excellent service, chauffeur très professionnel",
    "punctuality": 5,
    "driving_quality": 5,
    "vehicle_cleanliness": 4,
    "communication": 5,
    "tags": ["Ponctuel", "Conduite sûre", "Professionnel"],
    "is_anonymous": false
}

// Response
{
    "success": true,
    "message": "Merci pour votre évaluation",
    "rating": {
        "id": 1,
        "score": 5,
        "comment": "Excellent service, chauffeur très professionnel"
    }
}
```

### 7. Get Order History
**GET** `/api/v1/order/customer/order/history/?page=1&page_size=20`
```json
// Response
{
    "success": true,
    "total": 25,
    "page": 1,
    "page_size": 20,
    "orders": [
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "driver_name": "John Doe",
            "pickup_address": "Akwa, Douala",
            "destination_address": "Bonanjo, Douala",
            "final_price": "2875.50",
            "status": "COMPLETED",
            "created_at": "2024-01-15T09:00:00Z",
            "customer_rating": 5,
            "duration_minutes": 25
        }
    ]
}
```

---

## 💳 PAYMENT ENDPOINTS

### 1. Process Payment
**POST** `/api/v1/order/order/{order_id}/payment/`
```json
// Request
{
    "payment_method_id": 2,  // Orange Money
    "transaction_reference": "OM123456789"
}

// Response
{
    "success": true,
    "message": "Paiement Orange Money simulé",
    "payment_status": "PAID",
    "transaction": {
        "success": true,
        "amount": 2875.50,
        "transaction_id": "SIM_123e4567_1705316400"
    }
}
```

---

## 📋 COMMON ENDPOINTS

### 1. Get Payment Methods
**GET** `/api/v1/order/payment-methods/`
```json
// Response
{
    "success": true,
    "payment_methods": [
        {
            "id": 1,
            "type": "CASH",
            "type_display": "Espèces",
            "name": "Espèces",
            "description": "Paiement en espèces directement au chauffeur",
            "icon": "💵",
            "is_active": true,
            "min_amount": "500.00",
            "max_amount": null
        },
        {
            "id": 2,
            "type": "OM",
            "type_display": "Orange Money",
            "name": "Orange Money",
            "description": "Paiement via Orange Money",
            "icon": "📱",
            "is_active": true,
            "min_amount": "100.00",
            "max_amount": "1000000.00"
        }
    ]
}
```

### 2. Get Available Vehicle Types
**POST** `/api/v1/order/vehicle-types/available/`
```json
// Request
{
    "pickup_latitude": 4.0511,
    "pickup_longitude": 9.7679,
    "radius_km": 5
}

// Response
{
    "success": true,
    "vehicle_types": [
        {
            "type": "Taxi Jaune",
            "count": 3,
            "nearest_distance": 0.5,
            "drivers": [1, 2, 3]
        },
        {
            "type": "Confort",
            "count": 2,
            "nearest_distance": 1.2,
            "drivers": [4, 5]
        }
    ]
}
```

### 3. Get Order Details
**GET** `/api/v1/order/order/{order_id}/`
```json
// Response
{
    "success": true,
    "order": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "customer_name": "Jane Smith",
        "driver_name": "John Doe",
        "pickup_address": "Akwa, Douala",
        "pickup_latitude": "4.0511",
        "pickup_longitude": "9.7679",
        "destination_address": "Bonanjo, Douala",
        "destination_latitude": "4.0300",
        "destination_longitude": "9.7100",
        "vehicle_type_name": "Taxi Jaune",
        "city_name": "Douala",
        "payment_method_name": "Espèces",
        "payment_status": "PAID",
        "estimated_distance_km": "8.50",
        "actual_distance_km": "8.70",
        "base_price": "500.00",
        "distance_price": "2125.00",
        "total_price": "2625.00",
        "final_price": "2875.50",
        "waiting_time": 5,
        "driver_rating": 5,
        "customer_rating": null,
        "status": "COMPLETED",
        "created_at": "2024-01-15T09:00:00Z",
        "completed_at": "2024-01-15T09:25:00Z"
    }
}
```

---

## 🔄 WebSocket Endpoints

### Driver WebSocket
```
ws://localhost:8000/ws/driver/{driver_id}/
```

### Customer WebSocket
```
ws://localhost:8000/ws/customer/{customer_id}/
```

### Messages Types

#### Driver → Server
```json
{
    "type": "location_update",
    "latitude": 4.0511,
    "longitude": 9.7679,
    "speed_kmh": 45.5
}
```

#### Server → Driver
```json
{
    "type": "new_order_request",
    "order_data": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "pickup_address": "Akwa, Douala",
        "destination_address": "Bonanjo, Douala",
        "estimated_price": 2625
    },
    "timeout": 30
}
```

#### Customer → Server
```json
{
    "type": "search_drivers",
    "pickup_lat": 4.0511,
    "pickup_lng": 9.7679,
    "destination_lat": 4.0300,
    "destination_lng": 9.7100
}
```

#### Server → Customer
```json
{
    "type": "driver_location_update",
    "order_id": "123e4567-e89b-12d3-a456-426614174000",
    "latitude": 4.0450,
    "longitude": 9.7500,
    "speed": 45.5
}
```

---

## 🧪 Testing avec cURL

### Login pour obtenir le token
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "237600000001",
    "password": "test123",
    "user_type": "driver"
  }'
```

### Passer en ligne (Driver)
```bash
curl -X POST http://localhost:8000/api/v1/order/driver/status/toggle/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Rechercher des chauffeurs (Customer)
```bash
curl -X POST http://localhost:8000/api/v1/order/customer/search-drivers/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "pickup_latitude": 4.0511,
    "pickup_longitude": 9.7679,
    "radius_km": 5
  }'
```

---

## 📊 Status Codes

- `200` : Succès
- `201` : Créé avec succès
- `400` : Erreur de validation / Bad Request
- `401` : Non authentifié
- `403` : Non autorisé
- `404` : Ressource non trouvée
- `500` : Erreur serveur

---

## 🔑 Notes importantes

1. **Authentification** : Tous les endpoints nécessitent un token Bearer
2. **UUIDs** : Les IDs des commandes sont des UUIDs
3. **Coordonnées** : Format décimal (ex: 4.0511, pas "4.0511")
4. **Montants** : En FCFA, format décimal
5. **Pagination** : Utilise `page` et `page_size`
6. **Filtres de date** : Format ISO 8601 (2024-01-15T10:30:00Z)
