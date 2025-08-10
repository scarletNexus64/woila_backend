# Documentation API WOILA Backend

## Vue d'ensemble

Cette documentation décrit les endpoints de l'API REST du backend WOILA. L'API utilise Django REST Framework et nécessite une authentification par token Bearer pour la plupart des endpoints.

## Base URL

```
http://http://82.25.95.77/api/v1/
```

## Authentification

L'API utilise une authentification par token Bearer. Après connexion, incluez le token dans les headers :

```
Authorization: Bearer YOUR_TOKEN_HERE
```

## Documentation interactive

- **Swagger UI** : `/api/docs/swagger/`
- **ReDoc** : `/api/docs/redoc/`
- **Schema** : `/api/schema/`

---

## 1. Authentification

### 1.1 Inscription Chauffeur

**Endpoint** : `POST /api/v1/auth/register/driver/`

**Auth** : Non requis

**Content-Type** : `multipart/form-data`

**Description** : Permet à un nouveau chauffeur de s'inscrire avec toutes ses informations personnelles. Utilisez un formulaire multipart pour uploader la photo de profil.

**Body** (formulaire multipart) :
- `phone_number` (string) : Numéro de téléphone (+237123456789)
- `password` (string) : Mot de passe (min 6 caractères)
- `confirm_password` (string) : Confirmation du mot de passe
- `name` (string) : Prénom
- `surname` (string) : Nom de famille
- `gender` (string) : Genre (M, F, O)
- `age` (integer) : Âge (18-80 ans)
- `birthday` (date) : Date de naissance (YYYY-MM-DD)
- `profile_picture` (file) : Photo de profil (optionnel, max 5MB, JPG/PNG/GIF/WebP uniquement)
- `referral_code` (string) : Code de parrainage (optionnel)

**Réponse (201)** :
```json
{
    "success": true,
    "message": "Inscription chauffeur réussie. Vous pouvez maintenant vous connecter.",
    "user_type": "driver",
    "user_id": 1,
    "user_info": {
        "id": 1,
        "name": "Jean",
        "surname": "Dupont",
        "phone_number": "+237123456789",
        "gender": "M",
        "age": 35,
        "birthday": "1988-05-15",
        "profile_picture_url": "http://localhost:8000/media/profile_pictures/driver/1/photo.jpg"
    }
}
```

### 1.2 Inscription Client

**Endpoint** : `POST /api/v1/auth/register/customer/`

**Auth** : Non requis

**Content-Type** : `multipart/form-data`

**Description** : Permet à un nouveau client de s'inscrire avec ses informations de base. Utilisez un formulaire multipart pour uploader la photo de profil.

**Body** (formulaire multipart) :
- `phone_number` (string) : Numéro de téléphone (+237987654321)
- `password` (string) : Mot de passe (min 6 caractères)
- `confirm_password` (string) : Confirmation du mot de passe
- `name` (string) : Prénom
- `surname` (string) : Nom de famille
- `profile_picture` (file) : Photo de profil (optionnel, max 5MB, JPG/PNG/GIF/WebP uniquement)
- `referral_code` (string) : Code de parrainage (optionnel)

**Réponse (201)** :
```json
{
    "success": true,
    "message": "Inscription client réussie. Vous pouvez maintenant vous connecter.",
    "user_type": "customer",
    "user_id": 1,
    "user_info": {
        "id": 1,
        "name": "Marie",
        "surname": "Martin",
        "phone_number": "+237987654321",
        "profile_picture_url": "http://localhost:8000/media/profile_pictures/customer/1/photo.jpg"
    }
}
```

### 1.3 Connexion

**Endpoint** : `POST /api/v1/auth/login/`

**Auth** : Non requis

**Body** :
```json
{
    "phone_number": "+33123456789",
    "password": "motdepasse123",
    "user_type": "driver"  // driver ou customer
}
```

**Réponse (200)** :
```json
{
    "success": true,
    "message": "Connexion réussie",
    "token": "550e8400-e29b-41d4-a716-446655440000",
    "user_type": "driver",
    "user_id": 1,
    "user_info": {
        "id": 1,
        "name": "Jean",
        "surname": "Dupont",
        "phone_number": "+33123456789",
        "gender": "M",
        "age": 35,
        "birthday": "1988-05-15"
    }
}
```

### 1.4 Mot de Passe Oublié

**Endpoint** : `POST /api/v1/auth/forgot-password/`

**Auth** : Non requis

**Description** : Permet de réinitialiser le mot de passe d'un utilisateur en fournissant son numéro de téléphone et le nouveau mot de passe

**Body** :
```json
{
    "phone_number": "+237123456789",
    "new_password": "nouveaumotdepasse123",
    "user_type": "driver"  // driver ou customer
}
```

**Réponse (200)** :
```json
{
    "success": true,
    "message": "Mot de passe mis à jour avec succès"
}
```

**Réponse d'erreur (400)** :
```json
{
    "success": false,
    "message": "Données invalides",
    "errors": {
        "phone_number": ["Ce numéro de téléphone n'existe pas."]
    }
}
```

### 1.5 Déconnexion

**Endpoint** : `POST /api/v1/auth/logout/`

**Auth** : Token Bearer requis

**Body** :
```json
{
    "token": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Réponse (200)** :
```json
{
    "success": true,
    "message": "Déconnexion réussie"
}
```

---

## 2. Vérification OTP

### 2.1 Générer un Code OTP

**Endpoint** : `POST /api/v1/auth/generate-otp/`

**Auth** : Non requis

**Description** : Génère un code OTP à 4 chiffres et l'envoie par SMS ou WhatsApp au numéro fourni

**Body** :
```json
{
    "identifier": "+237123456789"
}
```

**Réponse (200)** :
```json
{
    "message": "Un code de vérification a été envoyé à votre numéro de téléphone.",
    "sms_sent": true,
    "identifier": "+237123456789"
}
```

**Réponse d'erreur (400)** :
```json
{
    "error": "Ce numéro est déjà utilisé"
}
```

### 2.2 Vérifier un Code OTP

**Endpoint** : `POST /api/v1/auth/verify-otp/`

**Auth** : Non requis

**Description** : Vérifie un code OTP envoyé précédemment

**Body** :
```json
{
    "identifier": "+237123456789",
    "otp": "1234"
}
```

**Réponse (200)** :
```json
{
    "status": "verified",
    "message": "Code OTP vérifié avec succès"
}
```

**Réponse d'erreur (400)** :
```json
{
    "error": "Code OTP invalide"
}
```

ou

```json
{
    "error": "Code OTP expiré ou déjà utilisé"
}
```

**Notes importantes** :
- Les codes OTP expirent après 5 minutes
- Un code OTP ne peut être utilisé qu'une seule fois
- Le système supporte l'envoi par SMS (Nexah) et WhatsApp (Meta)
- Pour les numéros de téléphone, le système vérifie s'ils ne sont pas déjà utilisés avant de générer l'OTP

---

## 3. Gestion des Tokens

### 3.1 Vérifier un Token

**Endpoint** : `POST /api/v1/auth/token/verify/`

**Auth** : Non requis

**Body** :
```json
{
    "token": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Réponse (200)** :
```json
{
    "success": true,
    "message": "Token valide",
    "user_type": "driver",
    "user_id": 1,
    "user_info": {
        "id": 1,
        "name": "Jean",
        "surname": "Dupont",
        "phone_number": "+33123456789",
        "gender": "M",
        "age": 35,
        "birthday": "1988-05-15"
    },
    "token_created_at": "2023-12-01T10:30:00Z"
}
```

### 3.2 Rafraîchir un Token

**Endpoint** : `POST /api/v1/auth/token/refresh/`

**Auth** : Non requis

**Body** :
```json
{
    "token": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Réponse (200)** :
```json
{
    "success": true,
    "message": "Token rafraîchi avec succès",
    "new_token": "550e8400-e29b-41d4-a716-446655440001",
    "user_type": "driver",
    "user_id": 1
}
```

---

## 4. Gestion des Documents

### 4.1 Importer des Documents

**Endpoint** : `POST /api/v1/documents/import/`

**Auth** : Token Bearer requis

**Content-Type** : `multipart/form-data`

**Body** :
- `user_id` (integer) : ID de l'utilisateur
- `user_type` (string) : "driver" ou "customer"
- `document_name` (string) : Nom du document (ex: "Permis de conduire")
- `file` (file) : Fichier unique à uploader
- `files` (files[]) : Plusieurs fichiers (optionnel)

**Réponse (201)** :
```json
{
    "success": true,
    "message": "Documents importés avec succès",
    "documents": [
        {
            "id": 1,
            "user_id": 1,
            "user_type": "driver",
            "user_info": "Jean Dupont (+33123456789)",
            "document_name": "Permis de conduire",
            "file_url": "http://localhost:8000/media/documents/driver/1/Permis%20de%20conduire/permis.jpg",
            "original_filename": "permis.jpg",
            "file_size": 245678,
            "content_type": "image/jpeg",
            "uploaded_at": "2023-12-01T10:30:00Z",
            "is_active": true
        }
    ]
}
```

### 4.2 Lister les Documents

**Endpoint** : `GET /api/v1/documents/list/`

**Auth** : Token Bearer requis

**Query Parameters** :
- `user_id` (integer) : Filtrer par ID utilisateur
- `user_type` (string) : Filtrer par type ("driver" ou "customer")
- `document_name` (string) : Filtrer par nom de document
- `is_active` (boolean) : Filtrer par statut actif

**Réponse (200)** :
```json
{
    "success": true,
    "count": 2,
    "documents": [
        {
            "id": 1,
            "user_id": 1,
            "user_type": "driver",
            "user_info": "Jean Dupont (+33123456789)",
            "document_name": "Permis de conduire",
            "file_url": "http://localhost:8000/media/documents/driver/1/Permis%20de%20conduire/permis.jpg",
            "original_filename": "permis.jpg",
            "file_size": 245678,
            "content_type": "image/jpeg",
            "uploaded_at": "2023-12-01T10:30:00Z",
            "is_active": true
        }
    ]
}
```

---

## 5. Gestion des Véhicules

### 5.1 Créer un Véhicule

**Endpoint** : `POST /api/v1/vehicles/create/`

**Auth** : Token Bearer requis

**Content-Type** : `multipart/form-data`

**Description** : Permet à un chauffeur de créer un véhicule avec ses informations et photos. Supporte l'upload de 4 images : 2 extérieures et 2 intérieures. 

⚠️ **IMPORTANT** : Le véhicule est créé avec `is_active=False` par défaut. L'administrateur doit l'activer manuellement dans le panel admin.

**Body** :
- `driver_id` (integer) : ID du chauffeur
- `vehicle_type_id` (integer) : ID du type de véhicule
- `brand_id` (integer) : ID de la marque
- `model_id` (integer) : ID du modèle
- `color_id` (integer) : ID de la couleur
- `nom` (string) : Nom du véhicule
- `plaque_immatriculation` (string) : Plaque d'immatriculation
- `etat_vehicule` (integer) : État du véhicule (1-10)
- `photo_exterieur_1` (file) : Photo extérieure 1 (optionnel)
- `photo_exterieur_2` (file) : Photo extérieure 2 (optionnel)
- `photo_interieur_1` (file) : Photo intérieure 1 (optionnel)
- `photo_interieur_2` (file) : Photo intérieure 2 (optionnel)

**Réponse (201)** :
```json
{
    "success": true,
    "message": "Véhicule créé avec succès. En attente d'activation par l'administrateur.",
    "vehicle": {
        "id": 1,
        "driver": 1,
        "driver_info": "Jean Dupont (+33123456789)",
        "vehicle_type": {
            "id": 1,
            "name": "Berline",
            "additional_amount": "1000.00",
            "is_active": true
        },
        "brand": {
            "id": 1,
            "name": "Toyota",
            "is_active": true
        },
        "model": {
            "id": 1,
            "name": "Corolla",
            "brand": {
                "id": 1,
                "name": "Toyota",
                "is_active": true
            },
            "is_active": true
        },
        "color": {
            "id": 1,
            "name": "Noir",
            "is_active": true
        },
        "nom": "Corolla 2020",
        "plaque_immatriculation": "AB-123-CD",
        "etat_vehicule": 8,
        "etat_display": "8/10",
        "images_urls": {
            "photo_exterieur_1": "http://localhost:8000/media/vehicles/1/1/photo1.jpg",
            "photo_exterieur_2": null,
            "photo_interieur_1": null,
            "photo_interieur_2": null
        },
        "created_at": "2023-12-01T10:30:00Z",
        "updated_at": "2023-12-01T10:30:00Z",
        "is_active": false
    }
}
```

### 5.2 Lister les Véhicules

**Endpoint** : `GET /api/v1/vehicles/`

**Auth** : Token Bearer requis

**Query Parameters** :
- `driver_id` (integer) : Filtrer par chauffeur
- `is_active` (boolean) : Filtrer par statut actif
- `plaque_immatriculation` (string) : Rechercher par plaque

**Réponse (200)** :
```json
{
    "success": true,
    "count": 2,
    "vehicles": [
        {
            "id": 1,
            "driver": 1,
            "driver_info": "Jean Dupont (+33123456789)",
            "vehicle_type": {
                "id": 1,
                "name": "Berline",
                "additional_amount": "1000.00",
                "is_active": true
            },
            "brand": {
                "id": 1,
                "name": "Toyota",
                "is_active": true
            },
            "model": {
                "id": 1,
                "name": "Corolla",
                "brand": {
                    "id": 1,
                    "name": "Toyota",
                    "is_active": true
                },
                "is_active": true
            },
            "color": {
                "id": 1,
                "name": "Noir",
                "is_active": true
            },
            "nom": "Corolla 2020",
            "plaque_immatriculation": "AB-123-CD",
            "etat_vehicule": 8,
            "etat_display": "8/10",
            "images_urls": {
                "photo_exterieur_1": "http://localhost:8000/media/vehicles/1/1/photo1.jpg",
                "photo_exterieur_2": null,
                "photo_interieur_1": null,
                "photo_interieur_2": null
            },
            "created_at": "2023-12-01T10:30:00Z",
            "updated_at": "2023-12-01T10:30:00Z",
            "is_active": true
        }
    ]
}
```

### 5.3 Détails d'un Véhicule

**Endpoint** : `GET /api/v1/vehicles/{vehicle_id}/`

**Auth** : Token Bearer requis

**Réponse (200)** : Même structure que pour un véhicule dans la liste

### 5.4 Véhicules par Chauffeur

**Endpoint** : `GET /api/v1/vehicles/driver/{driver_id}/`

**Auth** : Token Bearer requis

**Réponse (200)** : Liste des véhicules du chauffeur

### 5.5 Configurations Véhicules

#### Types de Véhicules
**Endpoint** : `GET /api/v1/vehicles/configs/types/`

**Auth** : Token Bearer requis

**Réponse (200)** :
```json
[
    {
        "id": 1,
        "name": "Berline",
        "additional_amount": "1000.00",
        "is_active": true
    },
    {
        "id": 2,
        "name": "SUV",
        "additional_amount": "2000.00",
        "is_active": true
    }
]
```

#### Marques de Véhicules
**Endpoint** : `GET /api/v1/vehicles/configs/brands/`

**Auth** : Token Bearer requis

**Réponse (200)** :
```json
[
    {
        "id": 1,
        "name": "Toyota",
        "is_active": true
    },
    {
        "id": 2,
        "name": "Mercedes",
        "is_active": true
    }
]
```

#### Modèles de Véhicules
**Endpoint** : `GET /api/v1/vehicles/configs/models/`

**Auth** : Token Bearer requis

**Query Parameters** :
- `brand_id` (integer) : Filtrer par marque

**Réponse (200)** :
```json
[
    {
        "id": 1,
        "name": "Corolla",
        "brand": {
            "id": 1,
            "name": "Toyota",
            "is_active": true
        },
        "is_active": true
    }
]
```

#### Couleurs de Véhicules
**Endpoint** : `GET /api/v1/vehicles/configs/colors/`

**Auth** : Token Bearer requis

**Réponse (200)** :
```json
[
    {
        "id": 1,
        "name": "Noir",
        "is_active": true
    },
    {
        "id": 2,
        "name": "Blanc",
        "is_active": true
    }
]
```

---

## 6. Gestion des Profils

### 6.1 Profil Chauffeur

**Endpoint** : `GET /api/v1/profiles/driver/{driver_id}/`

**Auth** : Token Bearer requis

**Réponse (200)** :
```json
{
    "success": true,
    "driver": {
        "id": 1,
        "phone_number": "+237123456789",
        "name": "Jean",
        "surname": "Dupont",
        "gender": "M",
        "age": 35,
        "birthday": "1988-05-15",
        "profile_picture_url": "http://localhost:8000/media/profile_pictures/driver/1/photo.jpg",
        "vehicles_count": 2,
        "documents_count": 3,
        "created_at": "2023-12-01T10:30:00Z",
        "updated_at": "2023-12-01T10:30:00Z",
        "is_active": true
    }
}
```

**Mise à jour** : `PUT /api/v1/profiles/driver/{driver_id}/`

**Content-Type** : `multipart/form-data`

**Description** : Modifie les informations personnelles d'un chauffeur. Utilisez un formulaire multipart pour uploader une nouvelle photo de profil.

**Body** (formulaire multipart) :
- `name` (string) : Prénom
- `surname` (string) : Nom de famille
- `gender` (string) : Genre (M, F, O)
- `age` (integer) : Âge (18-80 ans)
- `birthday` (date) : Date de naissance (YYYY-MM-DD)
- `phone_number` (string) : Numéro de téléphone
- `profile_picture` (file) : Nouvelle photo de profil (optionnel, max 5MB, JPG/PNG/GIF/WebP uniquement)

### 6.2 Profil Client

**Endpoint** : `GET /api/v1/profiles/customer/{customer_id}/`

**Auth** : Token Bearer requis

**Réponse (200)** :
```json
{
    "success": true,
    "customer": {
        "id": 1,
        "phone_number": "+237987654321",
        "name": "Marie",
        "surname": "Martin",
        "profile_picture_url": "http://localhost:8000/media/profile_pictures/customer/1/photo.jpg",
        "documents_count": 1,
        "created_at": "2023-12-01T10:30:00Z",
        "updated_at": "2023-12-01T10:30:00Z",
        "is_active": true
    }
}
```

**Mise à jour** : `PUT /api/v1/profiles/customer/{customer_id}/`

**Content-Type** : `multipart/form-data`

**Description** : Modifie les informations personnelles d'un client. Utilisez un formulaire multipart pour uploader une nouvelle photo de profil.

**Body** (formulaire multipart) :
- `name` (string) : Prénom
- `surname` (string) : Nom de famille
- `phone_number` (string) : Numéro de téléphone
- `profile_picture` (file) : Nouvelle photo de profil (optionnel, max 5MB, JPG/PNG/GIF/WebP uniquement)

### 6.3 Liste des Chauffeurs

**Endpoint** : `GET /api/v1/profiles/drivers/`

**Auth** : Token Bearer requis

**Query Parameters** :
- `is_active` (boolean) : Filtrer par statut actif
- `search` (string) : Rechercher par nom, prénom ou téléphone

**Réponse (200)** :
```json
{
    "success": true,
    "count": 10,
    "drivers": [
        {
            "id": 1,
            "phone_number": "+33123456789",
            "name": "Jean",
            "surname": "Dupont",
            "gender": "M",
            "age": 35,
            "birthday": "1988-05-15",
            "vehicles_count": 2,
            "documents_count": 3,
            "created_at": "2023-12-01T10:30:00Z",
            "updated_at": "2023-12-01T10:30:00Z",
            "is_active": true
        }
    ]
}
```

### 6.4 Liste des Clients

**Endpoint** : `GET /api/v1/profiles/customers/`

**Auth** : Token Bearer requis

**Query Parameters** :
- `is_active` (boolean) : Filtrer par statut actif
- `search` (string) : Rechercher par nom, prénom ou téléphone

**Réponse (200)** :
```json
{
    "success": true,
    "count": 5,
    "customers": [
        {
            "id": 1,
            "phone_number": "+33987654321",
            "name": "Marie",
            "surname": "Martin",
            "documents_count": 1,
            "created_at": "2023-12-01T10:30:00Z",
            "updated_at": "2023-12-01T10:30:00Z",
            "is_active": true
        }
    ]
}
```

---

## 7. Système de Parrainage

### 7.1 Valider un Code de Parrainage

**Endpoint** : `POST /api/v1/referral/validate-code/`

**Auth** : Non requis

**Body** :
```json
{
    "referral_code": "ABC12345"
}
```

**Réponse (200)** :
```json
{
    "valid": true,
    "referral_code": "ABC12345",
    "sponsor_info": "Jean Dupont (+33123456789)",
    "welcome_bonus_amount": 5000,
    "message": "✅ Code valide! Vous recevrez 5000 FCFA en bonus de bienvenue."
}
```

### 7.2 Informations de Parrainage d'un Utilisateur

**Endpoint** : `GET /api/v1/referral/user-info/`

**Auth** : Token Bearer requis

**Query Parameters** :
- `user_type` (string) : "driver" ou "customer" (requis)
- `user_id` (integer) : ID de l'utilisateur
- `phone_number` (string) : Numéro de téléphone (alternative à user_id)

**Réponse (200)** :
```json
{
    "referral_code": "ABC12345",
    "wallet_balance": "15000.00",
    "welcome_bonus_amount": 5000,
    "referral_system_active": true,
    "user_info": "Jean Dupont (+33123456789)",
    "user_type": "driver",
    "code_active": true,
    "created_at": "2023-12-01T10:30:00Z"
}
```

### 7.3 Wallet d'un Utilisateur

**Endpoint** : `GET /api/v1/referral/wallet/`

**Auth** : Token Bearer requis

**Query Parameters** :
- `user_type` (string) : "driver" ou "customer" (requis)
- `user_id` (integer) : ID de l'utilisateur (requis)

**Réponse (200)** :
```json
{
    "balance": "15000.00",
    "balance_formatted": "15 000 FCFA",
    "user_info": "Jean Dupont (+33123456789)",
    "created_at": "2023-12-01T10:30:00Z",
    "updated_at": "2023-12-01T10:30:00Z"
}
```

### 7.4 Statistiques du Système de Parrainage

**Endpoint** : `GET /api/v1/referral/stats/`

**Auth** : Token Bearer requis

**Réponse (200)** :
```json
{
    "total_referrals": 150,
    "active_referrals": 140,
    "total_bonus_distributed": "750000.00",
    "welcome_bonus_amount": 5000
}
```

---

## 8. WebSocket - Gestion des Commandes (Order)

### 8.1 Connexion WebSocket

**URL** : `ws://localhost:8000/ws/order/`

L'app `order` est configurée pour les WebSockets mais les endpoints REST ne sont pas encore implémentés.

---

## 10. Gestion des Notifications

### 10.1 Lister les Notifications

**Endpoint** : `GET /api/v1/notifications/`

**Auth** : Token Bearer requis

**Description** : Récupère toutes les notifications de l'utilisateur connecté

**Query Parameters** :
- `include_read` (boolean) : Inclure les notifications lues (défaut: true)
- `limit` (integer) : Nombre maximum de notifications à retourner (défaut: 50)

**Réponse (200)** :
```json
{
    "success": true,
    "count": 5,
    "unread_count": 2,
    "notifications": [
        {
            "id": 1,
            "title": "🎉 Bienvenue sur WOILA !",
            "content": "Bonjour Jean, Bienvenue dans la famille WOILA !...",
            "notification_type": "welcome",
            "type_display": "Notification de bienvenue",
            "is_read": false,
            "is_deleted": false,
            "metadata": {},
            "created_at": "2024-01-15T10:30:00Z",
            "read_at": null,
            "deleted_at": null,
            "user_display": "Jean Dupont",
            "is_new": true
        }
    ]
}
```

### 10.2 Notifications Non Lues

**Endpoint** : `GET /api/v1/notifications/unread/`

**Auth** : Token Bearer requis

**Description** : Récupère uniquement les notifications non lues de l'utilisateur

**Réponse (200)** :
```json
{
    "success": true,
    "count": 2,
    "notifications": [
        {
            "id": 1,
            "title": "🎉 Bienvenue sur WOILA !",
            "content": "Bonjour Jean, Bienvenue dans la famille WOILA !...",
            "notification_type": "welcome",
            "type_display": "Notification de bienvenue",
            "is_read": false,
            "is_deleted": false,
            "metadata": {},
            "created_at": "2024-01-15T10:30:00Z",
            "read_at": null,
            "deleted_at": null,
            "user_display": "Jean Dupont",
            "is_new": true
        }
    ]
}
```

### 10.3 Détail d'une Notification

**Endpoint** : `GET /api/v1/notifications/{notification_id}/`

**Auth** : Token Bearer requis

**Description** : Récupère les détails d'une notification spécifique

**Réponse (200)** :
```json
{
    "success": true,
    "notification": {
        "id": 1,
        "title": "🎉 Bienvenue sur WOILA !",
        "content": "Bonjour Jean, Bienvenue dans la famille WOILA !...",
        "notification_type": "welcome",
        "type_display": "Notification de bienvenue",
        "is_read": false,
        "is_deleted": false,
        "metadata": {},
        "created_at": "2024-01-15T10:30:00Z",
        "read_at": null,
        "deleted_at": null,
        "user_display": "Jean Dupont",
        "is_new": true
    }
}
```

### 10.4 Marquer une Notification comme Lue

**Endpoint** : `PATCH /api/v1/notifications/{notification_id}/`

**Auth** : Token Bearer requis

**Description** : Marque une notification spécifique comme lue

**Réponse (200)** :
```json
{
    "success": true,
    "message": "Notification marquée comme lue"
}
```

**Réponse d'erreur (400)** :
```json
{
    "success": false,
    "error": "Impossible de marquer la notification comme lue"
}
```

### 10.5 Supprimer une Notification

**Endpoint** : `DELETE /api/v1/notifications/{notification_id}/`

**Auth** : Token Bearer requis

**Description** : Supprime définitivement une notification (soft delete)

**Réponse (200)** :
```json
{
    "success": true,
    "message": "Notification supprimée"
}
```

**Réponse d'erreur (400)** :
```json
{
    "success": false,
    "error": "Impossible de supprimer la notification"
}
```

### 10.6 Marquer Toutes les Notifications comme Lues

**Endpoint** : `POST /api/v1/notifications/mark-all-read/`

**Auth** : Token Bearer requis

**Description** : Marque toutes les notifications de l'utilisateur comme lues

**Réponse (200)** :
```json
{
    "success": true,
    "message": "3 notification(s) marquée(s) comme lue(s)",
    "updated_count": 3
}
```

### 10.7 Statistiques des Notifications

**Endpoint** : `GET /api/v1/notifications/stats/`

**Auth** : Token Bearer requis

**Description** : Obtient les statistiques des notifications de l'utilisateur

**Réponse (200)** :
```json
{
    "success": true,
    "stats": {
        "total": 15,
        "unread": 3,
        "today": 2,
        "this_week": 7,
        "by_type": {
            "welcome": 1,
            "referral_used": 2,
            "vehicle_approved": 1,
            "system": 11,
            "order": 0,
            "other": 0
        }
    }
}
```

### Types de Notifications

Le système supporte les types de notifications suivants :

- **welcome** : Notification de bienvenue (envoyée lors de l'inscription)
- **referral_used** : Code parrain utilisé (envoyée au parrain quand son code est utilisé)
- **vehicle_approved** : Véhicule approuvé (envoyée au chauffeur quand son véhicule est activé)
- **system** : Notification système (messages administratifs)
- **order** : Notifications liées aux commandes
- **other** : Autres notifications

### Métadonnées des Notifications

Le champ `metadata` peut contenir des données supplémentaires selon le type :

- **referral_used** : `{"referral_code": "ABC123", "referred_user_info": "..."}`
- **vehicle_approved** : `{"vehicle_id": 1, "vehicle_name": "Toyota Corolla"}`
- **order** : `{"order_id": 1, "order_status": "completed"}`

---

## Codes d'Erreur

### Erreurs HTTP Standard

- `200 OK` : Requête réussie
- `201 Created` : Ressource créée avec succès
- `400 Bad Request` : Données invalides
- `401 Unauthorized` : Token invalide ou expiré
- `403 Forbidden` : Accès refusé
- `404 Not Found` : Ressource introuvable
- `500 Internal Server Error` : Erreur serveur

### Format des Erreurs

```json
{
    "success": false,
    "errors": {
        "field_name": ["Message d'erreur"],
        "another_field": ["Autre erreur"]
    }
}
```

---

## Notes Importantes

1. **Authentification** : Tous les endpoints sauf ceux d'inscription et de connexion nécessitent un token Bearer dans les headers.

2. **Upload de fichiers** : Pour les endpoints qui acceptent des fichiers (documents, photos de véhicules), utilisez `multipart/form-data`.

3. **Filtrage** : La plupart des endpoints de liste supportent des query parameters pour filtrer les résultats.

4. **Pagination** : Non implémentée dans la version actuelle.

5. **CORS** : Configuré pour accepter toutes les origines en développement.

6. **Système de parrainage** : 
   - Chaque utilisateur reçoit automatiquement un code de parrainage unique à l'inscription
   - Le bonus de bienvenue est crédité au parrain quand un filleul s'inscrit avec son code
   - Le montant du bonus est configurable via GeneralConfig (clé: WELCOME_BONUS_AMOUNT)

7. **Configurations générales** : Le système utilise la table GeneralConfig pour stocker des paramètres modifiables sans redéploiement (bonus de parrainage, activation du système, etc.)

8. **Gestion des véhicules** :
   - Les véhicules sont créés avec `is_active=False` par défaut
   - L'administrateur doit les activer manuellement dans le panel admin après vérification
   - Seuls les véhicules actifs peuvent être utilisés pour les courses
   - Workflow : Création → Vérification admin → Activation → Utilisation

9. **Photos de profil** :
   - Supportées pour les chauffeurs et clients lors de l'inscription et modification de profil
   - Taille maximale : 5MB par image
   - Formats acceptés : JPG, PNG, GIF, WebP
   - Stockage : `/media/profile_pictures/{user_type}/{user_id}/`
   - URL accessible via le champ `profile_picture_url` dans les réponses API
   - La photo est optionnelle lors de l'inscription et peut être ajoutée/modifiée plus tard

---

## Exemples d'Utilisation

### Flux d'inscription avec parrainage

1. Valider le code de parrainage :
```bash
curl -X POST http://localhost:8000/api/v1/referral/validate-code/ \
  -H "Content-Type: application/json" \
  -d '{"referral_code": "ABC12345"}'
```

2. S'inscrire avec le code :
```bash
curl -X POST http://localhost:8000/api/v1/auth/register/driver/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+33123456789",
    "password": "password123",
    "confirm_password": "password123",
    "name": "Jean",
    "surname": "Dupont",
    "gender": "M",
    "age": 35,
    "birthday": "1988-05-15",
    "referral_code": "ABC12345"
  }'
```

### Flux d'authentification

1. Se connecter :
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+33123456789",
    "password": "password123",
    "user_type": "driver"
  }'
```

2. Utiliser le token pour les requêtes suivantes :
```bash
curl -X GET http://localhost:8000/api/v1/vehicles/ \
  -H "Authorization: Bearer 550e8400-e29b-41d4-a716-446655440000"
```

### 5.6 Modifier un Véhicule

**Endpoint** : `PUT /api/v1/vehicles/{vehicle_id}/update/`

**Auth** : Token Bearer requis

**Content-Type** : `multipart/form-data`

**Body** :
- `vehicle_type_id` (integer) : ID du type de véhicule (optionnel)
- `brand_id` (integer) : ID de la marque (optionnel)
- `model_id` (integer) : ID du modèle (optionnel)
- `color_id` (integer) : ID de la couleur (optionnel)
- `nom` (string) : Nom du véhicule (optionnel)
- `plaque_immatriculation` (string) : Plaque d'immatriculation (optionnel)
- `etat_vehicule` (integer) : État du véhicule (1-10) (optionnel)
- `photo_exterieur_1` (file) : Photo extérieure 1 (optionnel)
- `photo_exterieur_2` (file) : Photo extérieure 2 (optionnel)
- `photo_interieur_1` (file) : Photo intérieure 1 (optionnel)
- `photo_interieur_2` (file) : Photo intérieure 2 (optionnel)

**Réponse (200)** :
```json
{
    "success": true,
    "message": "Véhicule modifié avec succès",
    "vehicle": {
        "id": 1,
        "driver": 1,
        "driver_info": "Jean Dupont (+33123456789)",
        "vehicle_type": {
            "id": 1,
            "name": "Berline",
            "additional_amount": "1000.00",
            "is_active": true
        },
        "brand": {
            "id": 1,
            "name": "Toyota",
            "is_active": true
        },
        "model": {
            "id": 1,
            "name": "Corolla",
            "brand": {
                "id": 1,
                "name": "Toyota",
                "is_active": true
            },
            "is_active": true
        },
        "color": {
            "id": 1,
            "name": "Noir",
            "is_active": true
        },
        "nom": "Corolla 2020 Modifiée",
        "plaque_immatriculation": "AB-123-CD",
        "etat_vehicule": 9,
        "etat_display": "9/10",
        "images_urls": {
            "photo_exterieur_1": "http://localhost:8000/media/vehicles/1/1/photo1.jpg",
            "photo_exterieur_2": null,
            "photo_interieur_1": null,
            "photo_interieur_2": null
        },
        "created_at": "2023-12-01T10:30:00Z",
        "updated_at": "2023-12-01T15:45:00Z",
        "is_active": true
    }
}
```

### 5.7 Supprimer un Véhicule

**Endpoint** : `DELETE /api/v1/vehicles/{vehicle_id}/delete/`

**Auth** : Token Bearer requis

**Réponse (200)** :
```json
{
    "success": true,
    "message": "Véhicule supprimé avec succès"
}
```

### 5.8 Désactiver un Véhicule

**Endpoint** : `PATCH /api/v1/vehicles/{vehicle_id}/deactivate/`

**Auth** : Token Bearer requis

**Réponse (200)** :
```json
{
    "success": true,
    "message": "Véhicule désactivé avec succès",
    "vehicle": {
        "id": 1,
        "driver": 1,
        "driver_info": "Jean Dupont (+33123456789)",
        "vehicle_type": {
            "id": 1,
            "name": "Berline",
            "additional_amount": "1000.00",
            "is_active": true
        },
        "brand": {
            "id": 1,
            "name": "Toyota",
            "is_active": true
        },
        "model": {
            "id": 1,
            "name": "Corolla",
            "brand": {
                "id": 1,
                "name": "Toyota",
                "is_active": true
            },
            "is_active": true
        },
        "color": {
            "id": 1,
            "name": "Noir",
            "is_active": true
        },
        "nom": "Corolla 2020",
        "plaque_immatriculation": "AB-123-CD",
        "etat_vehicule": 8,
        "etat_display": "8/10",
        "images_urls": {
            "photo_exterieur_1": "http://localhost:8000/media/vehicles/1/1/photo1.jpg",
            "photo_exterieur_2": null,
            "photo_interieur_1": null,
            "photo_interieur_2": null
        },
        "created_at": "2023-12-01T10:30:00Z",
        "updated_at": "2023-12-01T16:00:00Z",
        "is_active": false
    }
}
```

### 5.9 Mettre en Service/Hors Service un Véhicule

**Endpoint** : `PATCH /api/v1/vehicles/{vehicle_id}/toggle-online/`

**Auth** : Token Bearer requis

**Description** : Met un véhicule en service (is_online=True) ou hors service (is_online=False). Cette API respecte les critères suivants :
- Le véhicule doit être actif (is_active=True) avant de pouvoir être mis en service
- Il ne peut y avoir qu'une seule voiture en service à la fois pour un chauffeur
- Si un véhicule est déjà en service, cette API le met hors service
- Si aucun véhicule n'est en service, cette API met le véhicule demandé en service

**Réponse (200) - Mise en service réussie** :
```json
{
    "success": true,
    "message": "Véhicule Toyota Corolla (AB-123-CD) mis en service avec succès",
    "vehicle": {
        "id": 1,
        "nom": "Corolla 2020",
        "plaque_immatriculation": "AB-123-CD",
        "is_active": true,
        "is_online": true
    }
}
```

**Réponse (200) - Mise hors service réussie** :
```json
{
    "success": true,
    "message": "Véhicule Toyota Corolla (AB-123-CD) mis hors service avec succès",
    "vehicle": {
        "id": 1,
        "nom": "Corolla 2020",
        "plaque_immatriculation": "AB-123-CD",
        "is_active": true,
        "is_online": false
    }
}
```

**Réponse d'erreur (400) - Véhicule inactif** :
```json
{
    "success": false,
    "message": "Ce véhicule doit être actif (is_active=True) avant de pouvoir être mis en service"
}
```

**Réponse d'erreur (400) - Autre véhicule déjà en service** :
```json
{
    "success": false,
    "message": "Un autre véhicule est déjà en service : Mercedes C180 (XY-456-ZA). Seul un véhicule peut être en service à la fois."
}
```

**Réponse d'erreur (404)** :
```json
{
    "success": false,
    "message": "Véhicule introuvable"
}
```

---

## 9. Gestion du Statut des Chauffeurs

### 9.1 Obtenir le Statut du Chauffeur

**Endpoint** : `GET /api/v1/order/driver/status/`

**Auth** : Token Bearer requis (chauffeur uniquement)

**Réponse (200)** :
```json
{
    "status": "ONLINE",
    "last_online": "2023-12-01T10:30:00Z",
    "last_location_update": "2023-12-01T10:25:00Z",
    "current_latitude": "3.848",
    "current_longitude": "11.502"
}
```

**Réponse (200) - Aucun statut trouvé** :
```json
{
    "status": "OFFLINE",
    "message": "Aucun statut trouvé"
}
```

### 9.2 Basculer le Statut du Chauffeur

**Endpoint** : `POST /api/v1/order/driver/status/toggle/`

**Auth** : Token Bearer requis (chauffeur uniquement)

**Description** : Bascule automatiquement entre ONLINE et OFFLINE

**Réponse (200) - Passage en ligne** :
```json
{
    "status": "ONLINE",
    "message": "Vous êtes maintenant en ligne",
    "last_online": "2023-12-01T10:30:00Z"
}
```

**Réponse (200) - Passage hors ligne** :
```json
{
    "status": "OFFLINE",
    "message": "Vous êtes maintenant hors ligne",
    "last_online": "2023-12-01T10:30:00Z"
}
```

### 9.3 Forcer le Passage en Mode ONLINE

**Endpoint** : `POST /api/v1/order/driver/status/online/`

**Auth** : Token Bearer requis (chauffeur uniquement)

**Réponse (200)** :
```json
{
    "status": "ONLINE",
    "message": "Vous êtes maintenant en ligne",
    "last_online": "2023-12-01T10:30:00Z"
}
```

### 9.4 Forcer le Passage en Mode OFFLINE

**Endpoint** : `POST /api/v1/order/driver/status/offline/`

**Auth** : Token Bearer requis (chauffeur uniquement)

**Réponse (200)** :
```json
{
    "status": "OFFLINE",
    "message": "Vous êtes maintenant hors ligne"
}
```

**Réponse (200) - Déjà hors ligne** :
```json
{
    "status": "OFFLINE",
    "message": "Déjà hors ligne"
}
```

**Réponse d'erreur (401)** :
```json
{
    "error": "Token invalide ou vous devez être un chauffeur"
}
```