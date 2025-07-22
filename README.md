# 🚗 Woilà Backend - API VTC

Backend API pour l'application VTC Woilà avec gestion des chauffeurs, clients, véhicules et système de configuration flexible.

## 🚀 Installation rapide

### Option 1: Installation automatique (recommandée)
```bash
git clone <votre-repo>
cd Backend
pip install -r requirements.txt
python3 scripts/setup_project.py
```

### Option 2: Installation manuelle
```bash
git clone <votre-repo>
cd Backend
pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py init_default_configs
python3 manage.py createsuperuser
python3 manage.py runserver
```

## ⚙️ Configurations par défaut

Le projet inclut **8 configurations essentielles** qui sont automatiquement chargées :

| Configuration | Clé | Valeur par défaut | Description |
|---------------|-----|-------------------|-------------|
| ⏰ Temps d'attente maximum | `MAX_WAITING_TIME` | 30 minutes | Temps max d'attente client |
| 🎁 Bonus de bienvenue | `WELCOME_BONUS_AMOUNT` | 5000 FCFA | Bonus nouveau client |
| 💳 Montant minimum de recharge | `MIN_RECHARGE_AMOUNT` | 1000 FCFA | Recharge minimum |
| 💸 Commission plateforme | `PLATFORM_COMMISSION_RATE` | 15% | Commission sur les courses |
| 📧 Email de support | `SUPPORT_EMAIL` | support@woila.app | Contact support |
| 📱 Mode maintenance | `MAINTENANCE_MODE` | false | Mode maintenance app |
| 🔐 Vérification OTP | `ENABLE_OTP_VERIFICATION` | true | Activation OTP |
| 🚗 État minimum véhicule | `MIN_VEHICLE_STATE` | 6/10 | État minimum requis |

### 🔧 Gestion des configurations

```bash
# Charger les configurations par défaut
python3 manage.py init_default_configs

# Réinitialiser toutes les configurations
python3 manage.py init_default_configs --force

# Affichage détaillé
python3 manage.py init_default_configs --verbose
```

## 🌐 Accès aux interfaces

- **API Documentation**: http://127.0.0.1:8000/api/swagger/
- **Admin Dashboard**: http://127.0.0.1:8000/admin/
- **Configurations**: http://127.0.0.1:8000/admin/api/generalconfig/

## 🎨 Interface Admin

Le dashboard admin utilise **Jazzmin** avec :
- ✅ Thème sombre par défaut
- 🧡 Couleurs orange/rouge personnalisées
- 📱 Interface responsive et moderne
- 🎯 Emojis pour une meilleure UX
- 🔍 Recherche avancée et filtres

## 📊 Fonctionnalités principales

### 👥 Gestion des utilisateurs
- **Chauffeurs**: Inscription, profils, véhicules
- **Clients**: Inscription, profils, documents
- **Authentification**: Tokens JWT sécurisés

### 🚗 Gestion des véhicules
- Ajout avec photos (4 max)
- États de 1 à 10
- Validation des plaques d'immatriculation

### 📄 Gestion des documents
- Upload multiple de fichiers
- Support images et PDF
- Validation automatique des types

### 💰 Système économique
- Portefeuilles utilisateurs
- Codes de parrainage
- Configurations économiques flexibles

### ⚙️ Configurations dynamiques
- Système de configurations clé/valeur
- Types automatiques (numérique, booléen, texte)
- Interface admin intuitive avec emojis

## 🔄 Déploiement

Les configurations par défaut sont automatiquement chargées lors :
- ✅ Des migrations (`migrate`)
- ✅ De la commande `init_default_configs`
- ✅ Du script `setup_project.py`

Cela garantit que **vos 8 configurations essentielles** sont toujours présentes, même sur :
- 🌍 Nouveaux environnements de déploiement
- 👥 Clones du projet par d'autres développeurs
- 🔄 Réinitialisations de base de données

## 🛠️ Technologies utilisées

- **Django 5.2** - Framework web
- **Django REST Framework** - API REST
- **Jazzmin** - Interface admin moderne
- **SQLite** - Base de données (dev)
- **drf-spectacular** - Documentation API automatique

---

🚗 **Woilà Backend** - Plateforme VTC complète et moderne