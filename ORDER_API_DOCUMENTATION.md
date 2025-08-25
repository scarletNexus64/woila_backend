# Documentation API - Module Commande VTC

Cette documentation présente toutes les API du module de commande (order) de l'application Woila VTC, depuis la recherche de chauffeurs jusqu'au paiement.

## Table des matières

- [Architecture générale](#architecture-générale)
- [Authentification](#authentification)
- [API Chauffeur (Driver)](#api-chauffeur-driver)
- [API Client (Customer)](#api-client-customer)
- [API Paiement](#api-paiement)
- [API Communes](#api-communes)
- [Modèles de données](#modèles-de-données)
- [Services métier](#services-métier)
- [Gestion d'erreurs](#gestion-derreurs)

## Architecture générale

L'API suit une architecture RESTful avec trois catégories principales :
- **Driver** : APIs dédiées aux chauffeurs
- **Customer** : APIs dédiées aux clients
- **Common** : APIs communes aux deux types d'utilisateurs

### URL de base
```
/order/
```

## Authentification

Toutes les API utilisent l'authentification par Bearer Token :
```http
Authorization: Bearer <token>
```

Le token est vérifié via la table `Token` et détermine si l'utilisateur est un chauffeur ou un client.

## API Chauffeur (Driver)

### 1. Gestion du statut

#### Basculer le statut en ligne/hors ligne
```http
POST /order/driver/status/toggle/
```
**Description** : Permet au chauffeur de passer en ligne ou hors ligne

**Réponse** :
```json
{
  "success": true,
  "message": "Vous êtes maintenant en ligne",
  "status": "ONLINE",
  "data": {
    "id": 1,
    "driver": 123,
    "status": "ONLINE",
    "current_latitude": "14.6928",
    "current_longitude": "-17.4467",
    "last_online": "2024-01-15T10:30:00Z"
  }
}
```

#### Mettre en ligne (Legacy)
```http
POST /order/driver/status/online/
```

#### Mettre hors ligne (Legacy)
```http
POST /order/driver/status/offline/
```

#### Obtenir le statut actuel (Legacy)
```http
GET /order/driver/status/
```

### 2. Localisation GPS

#### Mettre à jour la position GPS
```http
POST /order/driver/location/update/
```

**Paramètres** :
```json
{
  "latitude": "14.6928",
  "longitude": "-17.4467",
  "speed_kmh": 45.5,
  "heading": 180,
  "accuracy": 10.0
}
```

**Réponse** :
```json
{
  "success": true,
  "message": "Position mise à jour",
  "current_location": {
    "latitude": 14.6928,
    "longitude": -17.4467,
    "last_update": "2024-01-15T10:30:00Z"
  }
}
```

### 3. Gestion des commandes

#### Accepter une commande
```http
POST /order/driver/order/<uuid:order_id>/accept/
```

**Description** : Accepte une commande proposée au chauffeur

**Réponse** :
```json
{
  "success": true,
  "message": "Commande acceptée avec succès",
  "order": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "ACCEPTED",
    "pickup_address": "Avenue Léopold Sédar Senghor, Dakar",
    "destination_address": "Plateau, Dakar",
    "total_price": 2500,
    "customer_name": "Amadou Diallo"
  }
}
```

#### Refuser une commande
```http
POST /order/driver/order/<uuid:order_id>/reject/
```

**Paramètres** :
```json
{
  "reason": "Embouteillage dans la zone"
}
```

#### Signaler l'arrivée au pickup
```http
POST /order/driver/order/<uuid:order_id>/arrived/
```

**Description** : Le chauffeur signale qu'il est arrivé au point de pickup

#### Démarrer la course
```http
POST /order/driver/order/<uuid:order_id>/start/
```

**Description** : Démarre la course après que le client soit monté

#### Terminer la course
```http
POST /order/driver/order/<uuid:order_id>/complete/
```

**Paramètres** :
```json
{
  "actual_distance_km": 12.5,
  "waiting_time": 5,
  "driver_notes": "Course terminée sans incident"
}
```

**Réponse** :
```json
{
  "success": true,
  "message": "Course terminée",
  "final_price": 2750,
  "order": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "COMPLETED",
    "final_price": 2750,
    "actual_distance_km": 12.5
  }
}
```

### 4. Historique et commande courante

#### Obtenir la commande en cours
```http
GET /order/driver/order/current/
```

**Réponse** :
```json
{
  "success": true,
  "order": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "IN_PROGRESS",
    "pickup_address": "Avenue Léopold Sédar Senghor",
    "destination_address": "Plateau",
    "customer_name": "Amadou Diallo",
    "started_at": "2024-01-15T11:00:00Z"
  }
}
```

#### Historique des courses
```http
GET /order/driver/order/history/
```

**Paramètres de requête** :
- `page` (int) : Numéro de page (défaut: 1)
- `page_size` (int) : Taille de page (défaut: 20)
- `date_from` (date) : Date de début
- `date_to` (date) : Date de fin
- `status` (string) : Filtrer par statut

**Réponse** :
```json
{
  "success": true,
  "total": 145,
  "page": 1,
  "page_size": 20,
  "orders": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "customer_name": "Amadou Diallo",
      "pickup_address": "Avenue Léopold Sédar Senghor",
      "destination_address": "Plateau",
      "total_price": 2500,
      "status": "COMPLETED",
      "created_at": "2024-01-15T10:00:00Z",
      "duration_minutes": 25,
      "driver_rating": 5
    }
  ]
}
```

## API Client (Customer)

### 1. Recherche et estimation

#### Rechercher des chauffeurs disponibles
```http
POST /order/customer/search-drivers/
```

**Paramètres** :
```json
{
  "pickup_latitude": "14.6928",
  "pickup_longitude": "-17.4467",
  "vehicle_type_id": 1,  // OPTIONNEL - si omis, retourne tous types
  "radius_km": 5
}
```

**Réponse** :
```json
{
  "success": true,
  "drivers_found": 8,
  "vehicle_types": [
    {
      "type": "Berline",
      "count": 5,
      "nearest_distance": 0.8
    },
    {
      "type": "SUV",
      "count": 3,
      "nearest_distance": 1.2
    }
  ],
  "drivers": [
    {
      "driver_id": 123,
      "driver_name": "Mamadou Kane",
      "distance_km": 0.8,
      "latitude": 14.6920,
      "longitude": -17.4470,
      "vehicle": {
        "type": "Berline",
        "plaque": "DK-2021-AA",
        "brand": "Toyota",
        "model": "Corolla",
        "color": "Blanche"
      },
      "rating": 4.8,
      "orders_today": 12
    }
  ]
}
```

#### Estimer le prix d'une course
```http
POST /order/customer/estimate-price/
```

**Paramètres** :
```json
{
  "pickup_latitude": "14.6928",
  "pickup_longitude": "-17.4467",
  "destination_latitude": "14.7167",
  "destination_longitude": "-17.4677",
  "vehicle_type_id": 1,
  "city_id": 1,
  "vip_zone_id": null
}
```

**Réponse** :
```json
{
  "success": true,
  "distance_km": 8.5,
  "price_estimate": {
    "min_price": 2200,
    "max_price": 2800,
    "estimated_price": 2500,
    "is_night_fare": false,
    "currency": "FCFA"
  }
}
```

### 2. Gestion des commandes

#### Créer une commande
```http
POST /order/customer/order/create/
```

**Paramètres** :
```json
{
  "pickup_address": "Avenue Léopold Sédar Senghor, Dakar",
  "pickup_latitude": "14.6928",
  "pickup_longitude": "-17.4467",
  "destination_address": "Plateau, Dakar",
  "destination_latitude": "14.7167",
  "destination_longitude": "-17.4677",
  "vehicle_type_id": 1,
  "city_id": 1,
  "vip_zone_id": null,
  "payment_method_id": 1,
  "customer_notes": "Merci d'appeler en arrivant"
}
```

**Réponse** :
```json
{
  "success": true,
  "message": "Commande créée, recherche de chauffeur en cours",
  "order": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "PENDING",
    "pickup_address": "Avenue Léopold Sédar Senghor, Dakar",
    "destination_address": "Plateau, Dakar",
    "total_price": 2500,
    "estimated_distance_km": 8.5,
    "payment_method_name": "Orange Money",
    "created_at": "2024-01-15T10:00:00Z"
  },
  "drivers_contacted": 8
}
```

#### Annuler une commande
```http
POST /order/customer/order/<uuid:order_id>/cancel/
```

**Paramètres** :
```json
{
  "reason": "Changement de programme"
}
```

#### Suivre une commande
```http
GET /order/customer/order/<uuid:order_id>/track/
```

**Réponse** :
```json
{
  "success": true,
  "order": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "IN_PROGRESS",
    "driver_name": "Mamadou Kane",
    "driver_phone": "+221701234567",
    "vehicle": {
      "plaque": "DK-2021-AA",
      "brand": "Toyota",
      "model": "Corolla"
    }
  },
  "driver_location": {
    "latitude": 14.6925,
    "longitude": -17.4465,
    "last_update": "2024-01-15T11:05:00Z"
  },
  "tracking_events": [
    {
      "event_type": "TRIP_STARTED",
      "created_at": "2024-01-15T11:00:00Z",
      "notes": "Course démarrée"
    }
  ]
}
```

#### Noter une course
```http
POST /order/customer/order/<uuid:order_id>/rate/
```

**Paramètres** :
```json
{
  "score": 5,
  "comment": "Excellent chauffeur, très ponctuel et courtois",
  "punctuality": 5,
  "driving_quality": 5,
  "vehicle_cleanliness": 4,
  "communication": 5,
  "tags": ["Ponctuel", "Conduite sûre", "Véhicule propre"],
  "is_anonymous": false
}
```

**Réponse** :
```json
{
  "success": true,
  "message": "Merci pour votre évaluation",
  "rating": {
    "id": 456,
    "score": 5,
    "comment": "Excellent chauffeur...",
    "created_at": "2024-01-15T12:00:00Z"
  }
}
```

### 3. Historique

#### Historique des commandes du client
```http
GET /order/customer/order/history/
```
*Même format que l'historique chauffeur*

## API Paiement

#### Traiter un paiement
```http
POST /order/order/<uuid:order_id>/payment/
```

**Paramètres** :
```json
{
  "payment_method_id": 1,
  "transaction_reference": "OM123456789"
}
```

**Réponse** :
```json
{
  "success": true,
  "message": "Paiement effectué avec succès",
  "payment_status": "PAID",
  "transaction": {
    "amount": 2750,
    "method": "OM",
    "transaction_id": "TXN_550e8400_1642248000"
  }
}
```

## API Communes

### 1. Configuration

#### Liste des méthodes de paiement
```http
GET /order/payment-methods/
```

**Réponse** :
```json
{
  "success": true,
  "payment_methods": [
    {
      "id": 1,
      "type": "OM",
      "type_display": "Orange Money",
      "name": "Orange Money",
      "icon": "om-icon.png",
      "is_active": true,
      "min_amount": 100,
      "max_amount": 500000
    },
    {
      "id": 2,
      "type": "CASH",
      "type_display": "Espèces",
      "name": "Paiement en espèces",
      "is_active": true
    }
  ]
}
```

#### Types de véhicules disponibles
```http
POST /order/vehicle-types/available/
```

**Paramètres** :
```json
{
  "pickup_latitude": "14.6928",
  "pickup_longitude": "-17.4467",
  "radius_km": 5
}
```

### 2. Recherche géographique

#### Rechercher une ville par nom
```http
GET /order/search/cities/?name=Yaoundé
```

**Paramètres de requête** :
- `name` (string, requis) : Nom de la ville à rechercher
- `country` (string, optionnel) : Nom du pays pour filtrer

**Réponse** :
```json
{
  "success": true,
  "message": "2 ville(s) trouvée(s)",
  "cities": [
    {
      "id": 15,
      "name": "Yaoundé",
      "country": "Cameroun",
      "prix_jour": 200,
      "prix_nuit": 350,
      "full_name": "Yaoundé (Cameroun)"
    }
  ]
}
```

#### Rechercher une zone VIP par nom
```http
GET /order/search/vip-zones/?name=Airport
```

**Paramètres de requête** :
- `name` (string, requis) : Nom de la zone VIP à rechercher

**Réponse** :
```json
{
  "success": true,
  "message": "1 zone(s) VIP trouvée(s)",
  "zones": [
    {
      "id": 3,
      "name": "Airport Zone",
      "prix_jour": 500,
      "prix_nuit": 750,
      "kilometer_rules": [
        {
          "min_kilometers": 5.0,
          "prix_jour_per_km": 100,
          "prix_nuit_per_km": 150
        },
        {
          "min_kilometers": 10.0,
          "prix_jour_per_km": 80,
          "prix_nuit_per_km": 120
        }
      ]
    }
  ]
}
```

#### Lister toutes les villes actives
```http
GET /order/cities/
```

**Paramètres de requête** :
- `page` (int, optionnel) : Numéro de page (défaut: 1)
- `page_size` (int, optionnel) : Taille de page (défaut: 50)

#### Lister toutes les zones VIP actives
```http
GET /order/vip-zones/
```

### 3. Détails communs

#### Détails d'une commande
```http
GET /order/order/<uuid:order_id>/
```
*Accessible par le client ou le chauffeur concerné*

**Réponse** :
```json
{
  "success": true,
  "order": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "customer_name": "Amadou Diallo",
    "driver_name": "Mamadou Kane",
    "status": "COMPLETED",
    "pickup_address": "Avenue Léopold Sédar Senghor",
    "destination_address": "Plateau",
    "vehicle_type_name": "Berline",
    "city_name": "Dakar",
    "payment_method_name": "Orange Money",
    "total_price": 2500,
    "final_price": 2750,
    "actual_distance_km": 12.5,
    "waiting_time": 5,
    "driver_rating": 5,
    "customer_rating": null,
    "created_at": "2024-01-15T10:00:00Z",
    "completed_at": "2024-01-15T11:25:00Z"
  }
}
```

## Modèles de données

### Statuts des commandes
```
DRAFT → PENDING → ACCEPTED → DRIVER_ARRIVED → IN_PROGRESS → COMPLETED
              ↘       ↓             ↓
                 CANCELLED    CANCELLED
```

### Statuts de paiement
- `PENDING` : En attente
- `PROCESSING` : En traitement
- `PAID` : Payé
- `FAILED` : Échoué
- `REFUNDED` : Remboursé

### Types de paiement
- `CASH` : Espèces
- `OM` : Orange Money
- `MOMO` : MTN Mobile Money
- `WALLET` : Portefeuille

## Services métier

### PricingService
Calcule les prix avec :
- Prix de base (STD_PRICELIST_ORDER)
- Prix par kilomètre (PRICE_PER_KM)
- Prix additionnel véhicule
- Prix ville (jour/nuit)
- Prix zone VIP avec règles kilométriques
- Prix d'attente (après 5 minutes gratuites)

### OrderService
Gère :
- Recherche de chauffeurs par distance
- Création de commandes avec validation
- Calcul de distances réelles (Haversine/geopy)
- Transitions de statut validées

### DriverPoolService
Orchestre :
- Création du pool de chauffeurs par priorité
- Attribution séquentielle des commandes
- Gestion des timeouts (30s par défaut)
- Tracking des réponses

### PaymentService
Traite :
- Paiement en espèces (enregistrement)
- Paiement par portefeuille (débit/crédit)
- Mobile Money (simulation, TODO: intégration réelle)
- Remboursements automatiques

### TrackingService
Enregistre :
- Positions GPS pendant les courses
- Calcul de distances réelles parcourues
- Détection de déviations d'itinéraire
- Historique complet des trajets

## Gestion d'erreurs

### Codes d'erreur courants

**401 Unauthorized**
```json
{
  "error": "Authentification requise en tant que chauffeur"
}
```

**403 Forbidden**
```json
{
  "error": "Vous n'êtes pas autorisé à accepter cette commande"
}
```

**404 Not Found**
```json
{
  "error": "Commande non trouvée"
}
```

**400 Bad Request**
```json
{
  "error": "Type de véhicule invalide ou inactif"
}
```

### Validation des données
- Distance maximum : 100 km
- Coordonnées pickup ≠ destination
- Vérification des types de véhicules actifs
- Validation des villes et zones VIP actives

## WebSocket (Notifications temps réel)

Le système utilise Django Channels pour les notifications :

### Canaux
- `customer_{customer_id}` : Notifications client
- `driver_{driver_id}` : Notifications chauffeur

### Événements
- `order_accepted` : Commande acceptée
- `driver_arrived` : Chauffeur arrivé
- `trip_started` : Course démarrée
- `trip_completed` : Course terminée
- `new_order_request` : Nouvelle commande (chauffeur)
- `order_cancelled` : Commande annulée

---

*Documentation générée automatiquement à partir du code source du module order/*