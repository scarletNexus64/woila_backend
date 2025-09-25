# 🏗️ Architecture du Projet Woila Backend

## 📋 Vue d'ensemble

Le projet Woila Backend a été réorganisé pour suivre les meilleures pratiques Django avec une structure d'applications thématiques bien définie.

## 🎯 Applications Django

### 📱 Applications Organisées (Nouvelles)

#### 🔐 `authentication/`
**Responsabilité**: Gestion de l'authentification et des sessions
- **Modèles**: Token (depuis api.models)
- **Vues**: LoginView, RegisterView, LogoutView, OTPView, etc.
- **URLs**: `/api/auth/`

#### 👤 `users/`  
**Responsabilité**: Gestion des profils utilisateurs (chauffeurs et clients)
- **Modèles**: UserDriver, UserCustomer (depuis api.models)
- **Vues**: ProfileView, DriverProfileView, CustomerProfileView
- **URLs**: `/api/profiles/`, `/api/auth/me/`

#### 🚗 `vehicles/`
**Responsabilité**: Gestion des véhicules et configurations
- **Modèles**: Vehicle, VehicleType, VehicleBrand, etc. (depuis api.models)
- **Vues**: VehicleListView, VehicleCreateView, VehicleUpdateView
- **URLs**: `/api/vehicles/`

#### 🔔 `notifications/`
**Responsabilité**: Notifications push et FCM
- **Modèles**: Notification, FCMToken (depuis api.models)
- **Vues**: NotificationListView, FCMTokenRegisterView
- **URLs**: `/api/notifications/`, `/api/fcm/`

#### 💰 `wallet/`
**Responsabilité**: Gestion du portefeuille et transactions
- **Modèles**: Wallet, WalletTransaction (depuis api.models)
- **Vues**: WalletBalanceView, WalletDepositView, WalletWithdrawalView
- **URLs**: `/api/wallet/`

### 🏛️ Applications Légacy (Existantes)

#### 📊 `api/`
**Statut**: Legacy - contient tous les modèles actuels
- **Modèles**: Tous les modèles existants (UserDriver, UserCustomer, Vehicle, etc.)
- **ViewSets**: Structure basée sur des ViewSets (anti-pattern)
- **Note**: À migrer progressivement vers les nouvelles applications

#### 🚕 `order/`
**Statut**: Maintenue - logique métier complexe
- **Responsabilité**: Gestion des commandes VTC
- **Modèles**: PaymentMethod, Order, Trip, etc.
- **URLs**: `/api/` (endpoints order)

## 🔄 Convention de Nommage

### ✅ Bonnes Pratiques (Nouvelles Apps)
```python
# Views - Suffixe "View"
class LoginView(APIView)
class VehicleListView(APIView)
class NotificationDetailView(APIView)

# URLs - Verbes HTTP clairs
path('login/', views.LoginView.as_view(), name='login')
path('vehicles/', views.VehicleListView.as_view(), name='vehicle-list')
```

### ❌ Anti-Patterns (Legacy)
```python
# ViewSets - Éviter dans les nouvelles apps
class LoginViewSet(ViewSet)  # ❌ Pas une vraie ViewSet REST
class VehicleViewSet(ModelViewSet)  # ❌ Si pas CRUD complet
```

## 📍 Endpoints Existants - **NE PAS MODIFIER**

> ⚠️ **IMPORTANT**: Tous les endpoints ci-dessous sont intégrés en production et ne doivent pas être modifiés.

### 🔐 Authentication
- `POST /api/auth/login/`
- `POST /api/auth/register/driver/`
- `POST /api/auth/register/customer/`
- `POST /api/auth/logout/`
- `POST /api/auth/token/verify/`
- `POST /api/auth/token/refresh/`
- `POST /api/auth/generate-otp/`
- `POST /api/auth/verify-otp/`

### 👤 Users
- `GET /api/auth/me/`
- `GET /api/profiles/driver/{id}/`
- `GET /api/profiles/customer/{id}/`
- `GET /api/profiles/drivers/`
- `GET /api/profiles/customers/`

### 🚗 Vehicles
- `GET /api/vehicles/`
- `POST /api/vehicles/create/`
- `GET /api/vehicles/{id}/`
- `PUT /api/vehicles/{id}/update/`
- `DELETE /api/vehicles/{id}/delete/`

### 🔔 Notifications
- `GET /api/notifications/`
- `POST /api/fcm/register/`
- `GET /api/notifications/unread/`

### 💰 Wallet
- `GET /api/wallet/balance/`
- `POST /api/wallet/deposit/`
- `GET /api/wallet/transactions/`

## 🚀 Migration Strategy

### Phase 1 - Structure (✅ Completed)
- [x] Créer les nouvelles applications Django
- [x] Définir la structure URL organizée
- [x] Mettre à jour INSTALLED_APPS

### Phase 2 - Migration Graduelle
- [ ] Migrer la logique des ViewSets vers les nouvelles Views
- [ ] Conserver les URLs existants pour la compatibilité
- [ ] Ajouter des tests pour les nouveaux endpoints

### Phase 3 - Consolidation
- [ ] Migrer les modèles vers les bonnes applications
- [ ] Mise à jour des imports
- [ ] Dépréciation progressive de l'app `api/`

## 📂 Structure des Fichiers

```
woila_backend/
├── authentication/           # 🔐 Authentification
│   ├── views.py             # Views pour auth (pas ViewSets)
│   ├── urls.py              # Routes auth
│   └── models.py            # Futurs modèles auth
├── users/                   # 👤 Profils utilisateurs
│   ├── views.py             # Views pour profils
│   ├── urls.py              # Routes profils
│   └── models.py            # Futurs modèles users
├── vehicles/                # 🚗 Véhicules
├── notifications/           # 🔔 Notifications
├── wallet/                  # 💰 Portefeuille
├── api/                     # 🏛️ Legacy (à migrer)
└── order/                   # 🚕 Commandes (maintenue)
```

## 🎯 Objectifs

1. **Séparation des Responsabilités**: Chaque app a un domaine métier clair
2. **Convention Django**: Utilisation des Views au lieu des ViewSets inappropriés
3. **Maintien de la Compatibilité**: Aucun endpoint existant n'est cassé
4. **Migration Progressive**: Transition graduelle sans interruption de service

## 📝 Notes Importantes

- **Endpoints Existants**: Tous les endpoints actuels fonctionnent toujours
- **URLs Préservées**: Aucune URL n'a été modifiée pour maintenir la compatibilité
- **Modèles**: Restent dans `api/models.py` pour l'instant
- **ViewSets Legacy**: Conservés mais pas utilisés pour les nouvelles fonctionnalités