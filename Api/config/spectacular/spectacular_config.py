"""
Configuration pour drf-spectacular (Swagger/OpenAPI documentation)
"""

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import extend_schema_serializer
from drf_spectacular import openapi

# Configuration de base
SPECTACULAR_SETTINGS = {
    'TITLE': 'Woila API - Wallet System',
    'DESCRIPTION': """
# 🏦 API de Gestion de Portefeuille Électronique - Woila

## 📱 Description
API complète pour la gestion des portefeuilles électroniques des utilisateurs Woila (chauffeurs et clients).
Permet les dépôts, retraits et consultation de l'historique des transactions via Mobile Money (FreeMoPay).

## 🔐 Authentification

### Comment s'authentifier :
1. **Connexion** : Utilisez l'API `/api/v1/auth/login/` pour obtenir un token
2. **Utilisation** : Ajoutez le token dans l'en-tête Authorization de chaque requête

### Format du token :
```
Authorization: Bearer <votre_token>
```

### Exemple de connexion :
```bash
curl -X POST "http://your-domain.com/api/v1/auth/login/" \\
  -H "Content-Type: application/json" \\
  -d '{
    "phone_number": "+237690000000",
    "password": "votre_mot_de_passe",
    "user_type": "driver"
  }'
```

## 🚀 Comment tester dans cette interface :

1. **Connectez-vous** via l'API de login (hors de cette doc)
2. **Copiez le token** obtenu  
3. **Cliquez sur "Authorize"** 🔒 en haut à droite
4. **Entrez** : `Bearer <votre_token>`
5. **Testez les APIs** avec "Try it out"

## 💡 Points importants :

- **Polling automatique** : Les dépôts font du polling pendant 2 minutes max
- **Vérification du solde** : Impossible d'avoir un solde négatif
- **Transactions atomiques** : Sécurité garantie
- **Multi-utilisateurs** : Support chauffeurs et clients

## 📞 Support :
- Email: support@woila.cm
- Documentation complète disponible dans le projet
    """,
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'CONTACT': {
        'name': 'Équipe Woila',
        'email': 'support@woila.cm',
        'url': 'https://woila.cm'
    },
    'LICENSE': {
        'name': 'Propriétaire Woila',
        'url': 'https://woila.cm/license'
    },
    'EXTERNAL_DOCS': {
        'description': 'Documentation complète',
        'url': 'https://docs.woila.cm'
    },
    'TAGS': [
        {
            'name': '🏦 Wallet / Portefeuille',
            'description': 'Gestion du portefeuille électronique : dépôts, retraits, historique des transactions'
        },
        {
            'name': '🔐 Authentification', 
            'description': 'APIs de connexion et gestion des tokens'
        },
        {
            'name': '👥 Utilisateurs',
            'description': 'Gestion des profils chauffeurs et clients'
        }
    ],
    'COMPONENT_SPLIT_REQUEST': True,
    'COMPONENT_NO_READ_ONLY_REQUIRED': False,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': False,
        'defaultModelsExpandDepth': 2,
        'defaultModelExpandDepth': 2,
        'defaultModelRendering': 'example',
        'displayRequestDuration': True,
        'docExpansion': 'list',
        'filter': True,
        'operationsSorter': 'alpha',
        'showExtensions': True,
        'showCommonExtensions': True,
        'tagsSorter': 'alpha'
    },
    'REDOC_UI_SETTINGS': {
        'hideDownloadButton': False,
        'hideHostname': False,
        'hideLoading': False,
        'hideSchemaPattern': True,
        'hideSecuritySection': False,
        'noAutoAuth': False,
        'pathInMiddlePanel': False,
        'requiredPropsFirst': True,
        'scrollYOffset': 0,
        'showExtensions': True,
        'sortPropsAlphabetically': True,
        'suppressWarnings': False,
        'unstable_ignoreMimeTypeErrors': False
    },
    'SERVERS': [
        {
            'url': 'https://api.woila.cm',
            'description': 'Production server'
        },
        {
            'url': 'https://staging-api.woila.cm',
            'description': 'Staging server'
        },
        {
            'url': 'http://localhost:8000',
            'description': 'Development server'
        }
    ],
    'SECURITY': [
        {
            'BearerAuth': []
        }
    ],
    'COMPONENTS': {
        'securitySchemes': {
            'BearerAuth': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
                'description': 'Token d\'authentification obtenu via l\'API de login. Format: Bearer <token>'
            }
        }
    }
}

# Exemples de réponses communes
WALLET_EXAMPLES = {
    'balance_response': {
        'success': True,
        'balance': 15000.00,
        'user_type': 'driver',
        'user_id': 1
    },
    'deposit_request': {
        'amount': 10000.00,
        'phone_number': '+237690000000',
        'description': 'Rechargement wallet pour courses'
    },
    'deposit_response_success': {
        'success': True,
        'transaction_reference': 'DEP-20231201123045-A1B2C3D4',
        'freemopay_reference': 'FM123456789',
        'amount': 10000,
        'status': 'completed',
        'message': 'Dépôt initié avec succès',
        'final_result': {
            'status': 'SUCCESS',
            'final_status': 'SUCCESS', 
            'reason': 'Payment completed',
            'polling_duration': 45.2,
            'attempts': 23,
            'reference': 'FM123456789'
        }
    },
    'withdrawal_request': {
        'amount': 5000.00,
        'phone_number': '+237690000000',
        'description': 'Retrait vers Mobile Money'
    },
    'withdrawal_response_success': {
        'success': True,
        'transaction_reference': 'WIT-20231201123045-B5C6D7E8',
        'amount': 5000,
        'status': 'completed',
        'message': 'Retrait effectué avec succès',
        'new_balance': 10000.00
    },
    'error_response': {
        'success': False,
        'message': 'Solde insuffisant. Solde disponible: 3000.00 FCFA'
    },
    'transaction_history': {
        'success': True,
        'transactions': [
            {
                'id': 1,
                'reference': 'DEP-20231201123045-A1B2C3D4',
                'type': 'deposit',
                'type_display': 'Dépôt',
                'amount': 10000.0,
                'status': 'completed',
                'status_display': 'Complété',
                'payment_method': 'mobile_money',
                'phone_number': '+237690000000',
                'description': 'Dépôt de 10000 FCFA',
                'balance_before': 5000.0,
                'balance_after': 15000.0,
                'created_at': '2023-12-01T12:30:45.123456Z',
                'completed_at': '2023-12-01T12:32:15.789012Z',
                'error_message': None
            }
        ],
        'pagination': {
            'page': 1,
            'page_size': 20,
            'total_count': 1,
            'total_pages': 1
        },
        'current_balance': 15000.0
    }
}

def get_wallet_schema_extensions():
    """Extensions personnalisées pour les schémas Wallet"""
    return {
        'x-wallet-info': {
            'supported_currencies': ['FCFA'],
            'supported_payment_methods': ['mobile_money'],
            'polling_duration': '120 seconds',
            'polling_interval': '2 seconds',
            'minimum_amount': 100,
            'maximum_amount': 1000000
        },
        'x-freemopay-info': {
            'provider': 'FreeMoPay',
            'api_version': 'v2',
            'supported_operators': ['MTN', 'Orange', 'Camtel']
        }
    }