"""
Configuration et informations pour la documentation Swagger
"""

from drf_yasg import openapi

# Configuration de base pour Swagger
swagger_info = openapi.Info(
    title="Woila API - Wallet System",
    default_version='v1',
    description="""
# 🏦 API de Gestion de Portefeuille - Woila

## 📝 Description
API complète pour la gestion des portefeuilles électroniques des utilisateurs Woila (chauffeurs et clients).
Permet les dépôts, retraits et consultation de l'historique des transactions via Mobile Money (FreeMoPay).

## 🔐 Authentification

### Comment s'authentifier :
1. **Connexion** : Utilisez l'API `/api/auth/login/` pour obtenir un token
2. **Utilisation** : Ajoutez le token dans l'en-tête Authorization de chaque requête

### Format du token :
```
Authorization: Bearer <votre_token>
```

### Exemple de connexion :
```bash
curl -X POST "http://your-domain.com/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+237690000000",
    "password": "votre_mot_de_passe",
    "user_type": "driver"
  }'
```

### Réponse de connexion :
```json
{
  "success": true,
  "token": "abc123def456...",
  "user_type": "driver",
  "user_id": 1
}
```

## 🚀 Utilisation dans Swagger

### Pour tester les APIs dans cette interface :
1. **Connectez-vous d'abord** via l'API de login (non documentée ici)
2. **Copiez le token** obtenu
3. **Cliquez sur "Authorize"** 🔒 en haut à droite
4. **Entrez** : `Bearer <votre_token>`
5. **Testez les APIs** en cliquant sur "Try it out"

## 📊 Types d'utilisateurs supportés :
- **driver** : Chauffeurs Woila
- **customer** : Clients Woila

## 💰 Devises supportées :
- **FCFA** : Franc CFA (devise unique actuellement)

## 🎯 Fonctionnalités principales :
- ✅ Consultation du solde
- ✅ Dépôt d'argent via Mobile Money
- ✅ Retrait d'argent vers Mobile Money  
- ✅ Historique des transactions avec pagination
- ✅ Détails complets de chaque transaction
- ✅ Polling automatique pour confirmation des paiements

## 📱 Méthodes de paiement :
- **Mobile Money** : MTN, Orange Money, etc.
- **FreeMoPay** : Service de paiement intégré

## ⚡ Performance :
- **Polling automatique** : 2 minutes maximum
- **Vérifications en temps réel** du solde
- **Transactions atomiques** pour la sécurité

## 🔒 Sécurité :
- Authentification obligatoire pour toutes les APIs
- Validation stricte des montants
- Impossibilité d'avoir un solde négatif
- Audit complet de toutes les transactions
    """,
    terms_of_service="https://woila.cm/terms/",
    contact=openapi.Contact(email="support@woila.cm"),
    license=openapi.License(name="Propriétaire Woila"),
)

# Tags pour organiser les APIs
swagger_tags = [
    {
        "name": "🏦 Wallet / Portefeuille",
        "description": "APIs de gestion du portefeuille électronique : dépôts, retraits, consultations"
    }
]

# Paramètres de sécurité
swagger_security_definitions = {
    'Bearer': {
        'type': 'apiKey',
        'name': 'Authorization',
        'in': 'header',
        'description': 'Token d\'authentification au format: Bearer <token>'
    }
}

# Réponses d'erreur communes
common_error_responses = {
    401: "Token manquant, invalide ou expiré",
    403: "Accès refusé - permissions insuffisantes", 
    500: "Erreur interne du serveur",
    400: "Données de requête invalides"
}

# Exemples de données pour les tests
example_data = {
    "deposit_request": {
        "amount": 10000.00,
        "phone_number": "+237690000000",
        "description": "Rechargement wallet pour courses"
    },
    "withdrawal_request": {
        "amount": 5000.00,
        "phone_number": "+237690000000", 
        "description": "Retrait vers Mobile Money"
    },
    "transaction_reference": "DEP-20231201123045-A1B2C3D4",
    "balance_response": {
        "success": True,
        "balance": 15000.00,
        "user_type": "driver",
        "user_id": 1
    }
}