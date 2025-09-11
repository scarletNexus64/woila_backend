# FreeMoPay API Python Integration Documentation

## Aperçu et limitations actuelles

La documentation API FreeMoPay spécifiée n'est pas accessible publiquement. FreeMoPay semble être une plateforme de gestion de tontines numériques axée sur les marchés africains, nécessitant probablement un partenariat commercial pour l'accès API. Cette documentation fournit un guide d'intégration complet basé sur les meilleures pratiques de l'industrie des paiements.

## Table des matières

1. [Configuration initiale](#configuration-initiale)
2. [Authentification](#authentification)
3. [Endpoints principaux](#endpoints-principaux)
4. [Implémentation Python](#implémentation-python)
5. [Gestion des erreurs](#gestion-des-erreurs)
6. [Sécurité et bonnes pratiques](#sécurité-et-bonnes-pratiques)
7. [Exemples d'utilisation](#exemples-dutilisation)

## Configuration initiale

### Installation des dépendances

```bash
pip install requests python-dotenv cryptography retrying
```

### Structure du projet recommandée

```
freemopay_integration/
├── config/
│   ├── __init__.py
│   └── settings.py
├── freemopay/
│   ├── __init__.py
│   ├── client.py
│   ├── exceptions.py
│   ├── models.py
│   └── utils.py
├── tests/
│   └── test_client.py
├── .env
├── .gitignore
└── requirements.txt
```

## Authentification

### Configuration des variables d'environnement

Créez un fichier `.env` à la racine du projet:

```env
# FreeMoPay API Configuration
FREEMOPAY_API_KEY=your_api_key_here
FREEMOPAY_SECRET_KEY=your_secret_key_here
FREEMOPAY_MERCHANT_ID=your_merchant_id_here
FREEMOPAY_ENVIRONMENT=sandbox  # ou production
FREEMOPAY_WEBHOOK_SECRET=your_webhook_secret_here

# URLs de base
FREEMOPAY_SANDBOX_URL=https://sandbox.api.freemopay.com/v1
FREEMOPAY_PRODUCTION_URL=https://api.freemopay.com/v1

# Configuration de sécurité
FREEMOPAY_REQUEST_TIMEOUT=30
FREEMOPAY_MAX_RETRIES=3
```

### Module de configuration (config/settings.py)

```python
import os
from dotenv import load_dotenv
from enum import Enum

# Charger les variables d'environnement
load_dotenv()

class Environment(Enum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"

class FreeMoPayConfig:
    """Configuration centralisée pour l'API FreeMoPay"""
    
    def __init__(self):
        self.api_key = os.getenv('FREEMOPAY_API_KEY')
        self.secret_key = os.getenv('FREEMOPAY_SECRET_KEY')
        self.merchant_id = os.getenv('FREEMOPAY_MERCHANT_ID')
        self.webhook_secret = os.getenv('FREEMOPAY_WEBHOOK_SECRET')
        
        # Déterminer l'environnement
        env_str = os.getenv('FREEMOPAY_ENVIRONMENT', 'sandbox').lower()
        self.environment = Environment(env_str)
        
        # Définir l'URL de base selon l'environnement
        if self.environment == Environment.PRODUCTION:
            self.base_url = os.getenv('FREEMOPAY_PRODUCTION_URL')
        else:
            self.base_url = os.getenv('FREEMOPAY_SANDBOX_URL')
        
        # Paramètres de sécurité
        self.request_timeout = int(os.getenv('FREEMOPAY_REQUEST_TIMEOUT', 30))
        self.max_retries = int(os.getenv('FREEMOPAY_MAX_RETRIES', 3))
        
        # Validation
        self._validate_config()
    
    def _validate_config(self):
        """Valider que toutes les configurations requises sont présentes"""
        required_fields = ['api_key', 'secret_key', 'merchant_id', 'base_url']
        missing_fields = [field for field in required_fields 
                         if not getattr(self, field)]
        
        if missing_fields:
            raise ValueError(f"Configuration manquante: {', '.join(missing_fields)}")
```

## Endpoints principaux

### Structure des endpoints (basée sur les standards de l'industrie)

| Endpoint | Méthode | Description | Paramètres requis |
|----------|---------|-------------|-------------------|
| `/auth/token` | POST | Obtenir un token d'authentification | `api_key`, `secret_key` |
| `/deposits/initiate` | POST | Initier un dépôt | `amount`, `currency`, `phone_number`, `reference` |
| `/deposits/{id}/status` | GET | Vérifier le statut d'un dépôt | `deposit_id` |
| `/withdrawals/initiate` | POST | Initier un retrait | `amount`, `currency`, `phone_number`, `account_number` |
| `/withdrawals/{id}/status` | GET | Vérifier le statut d'un retrait | `withdrawal_id` |
| `/transactions` | GET | Liste des transactions | `page`, `limit`, `start_date`, `end_date` |
| `/balance` | GET | Obtenir le solde du compte | - |
| `/webhooks/validate` | POST | Valider une notification webhook | `signature`, `payload` |

## Implémentation Python

### Exceptions personnalisées (freemopay/exceptions.py)

```python
class FreeMoPayException(Exception):
    """Exception de base pour l'API FreeMoPay"""
    pass

class AuthenticationError(FreeMoPayException):
    """Erreur d'authentification"""
    pass

class ValidationError(FreeMoPayException):
    """Erreur de validation des données"""
    pass

class InsufficientFundsError(FreeMoPayException):
    """Fonds insuffisants"""
    pass

class NetworkError(FreeMoPayException):
    """Erreur de réseau"""
    pass

class RateLimitError(FreeMoPayException):
    """Limite de taux dépassée"""
    pass

class TransactionError(FreeMoPayException):
    """Erreur de transaction"""
    def __init__(self, message, error_code=None, transaction_id=None):
        super().__init__(message)
        self.error_code = error_code
        self.transaction_id = transaction_id
```

### Modèles de données (freemopay/models.py)

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class TransactionStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Currency(Enum):
    XAF = "XAF"  # Franc CFA
    EUR = "EUR"
    USD = "USD"

@dataclass
class DepositRequest:
    """Modèle pour une demande de dépôt"""
    amount: float
    currency: Currency
    phone_number: str
    reference: str
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def validate(self):
        """Valider les données de la demande"""
        if self.amount <= 0:
            raise ValidationError("Le montant doit être positif")
        if not self.phone_number:
            raise ValidationError("Le numéro de téléphone est requis")
        if len(self.reference) > 50:
            raise ValidationError("La référence ne doit pas dépasser 50 caractères")

@dataclass
class WithdrawalRequest:
    """Modèle pour une demande de retrait"""
    amount: float
    currency: Currency
    phone_number: str
    account_number: str
    reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def validate(self):
        """Valider les données de la demande"""
        if self.amount <= 0:
            raise ValidationError("Le montant doit être positif")
        if not self.phone_number:
            raise ValidationError("Le numéro de téléphone est requis")
        if not self.account_number:
            raise ValidationError("Le numéro de compte est requis")

@dataclass
class Transaction:
    """Modèle pour une transaction"""
    id: str
    type: str  # deposit ou withdrawal
    amount: float
    currency: Currency
    status: TransactionStatus
    created_at: datetime
    updated_at: datetime
    reference: Optional[str] = None
    phone_number: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
```

### Client principal (freemopay/client.py)

```python
import requests
import hashlib
import hmac
import json
import time
import logging
from typing import Optional, Dict, Any, List
from retrying import retry
from datetime import datetime
from urllib.parse import urljoin

from .exceptions import *
from .models import *
from config.settings import FreeMoPayConfig

logger = logging.getLogger(__name__)

class FreeMoPayClient:
    """Client principal pour l'API FreeMoPay"""
    
    def __init__(self, config: Optional[FreeMoPayConfig] = None):
        self.config = config or FreeMoPayConfig()
        self.session = requests.Session()
        self.access_token = None
        self.token_expiry = None
        
        # Configuration des headers par défaut
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-Merchant-ID': self.config.merchant_id,
            'User-Agent': 'FreeMoPay-Python-SDK/1.0.0'
        })
    
    def _generate_signature(self, payload: Dict[str, Any]) -> str:
        """Générer une signature HMAC pour sécuriser les requêtes"""
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            self.config.secret_key.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _ensure_authenticated(self):
        """S'assurer que le client est authentifié"""
        if not self.access_token or self._is_token_expired():
            self.authenticate()
    
    def _is_token_expired(self) -> bool:
        """Vérifier si le token est expiré"""
        if not self.token_expiry:
            return True
        return datetime.now() >= self.token_expiry
    
    @retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000)
    def _make_request(self, method: str, endpoint: str, 
                     data: Optional[Dict] = None, 
                     params: Optional[Dict] = None) -> Dict:
        """Effectuer une requête HTTP avec retry automatique"""
        url = urljoin(self.config.base_url, endpoint)
        
        # Ajouter l'authentification si nécessaire
        if endpoint != '/auth/token':
            self._ensure_authenticated()
            self.session.headers['Authorization'] = f'Bearer {self.access_token}'
        
        # Ajouter la signature pour les requêtes POST/PUT
        if method in ['POST', 'PUT'] and data:
            signature = self._generate_signature(data)
            self.session.headers['X-Signature'] = signature
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.config.request_timeout
            )
            
            # Gestion des codes de statut
            if response.status_code == 401:
                raise AuthenticationError("Authentification échouée")
            elif response.status_code == 403:
                raise AuthenticationError("Accès refusé")
            elif response.status_code == 429:
                raise RateLimitError("Limite de taux dépassée")
            elif response.status_code >= 500:
                raise NetworkError(f"Erreur serveur: {response.status_code}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Erreur de requête: {str(e)}")
            raise NetworkError(f"Erreur de connexion: {str(e)}")
    
    def authenticate(self) -> Dict:
        """S'authentifier auprès de l'API FreeMoPay"""
        payload = {
            'api_key': self.config.api_key,
            'secret_key': self.config.secret_key,
            'grant_type': 'client_credentials'
        }
        
        response = self._make_request('POST', '/auth/token', data=payload)
        
        self.access_token = response.get('access_token')
        expires_in = response.get('expires_in', 3600)
        self.token_expiry = datetime.now().timestamp() + expires_in
        
        logger.info("Authentification réussie")
        return response
    
    def initiate_deposit(self, deposit_request: DepositRequest) -> Transaction:
        """Initier un dépôt d'argent"""
        deposit_request.validate()
        
        payload = {
            'amount': deposit_request.amount,
            'currency': deposit_request.currency.value,
            'phone_number': deposit_request.phone_number,
            'reference': deposit_request.reference,
            'description': deposit_request.description,
            'metadata': deposit_request.metadata,
            'timestamp': int(time.time())
        }
        
        response = self._make_request('POST', '/deposits/initiate', data=payload)
        
        # Créer l'objet Transaction
        transaction = Transaction(
            id=response['transaction_id'],
            type='deposit',
            amount=response['amount'],
            currency=Currency(response['currency']),
            status=TransactionStatus(response['status']),
            created_at=datetime.fromisoformat(response['created_at']),
            updated_at=datetime.fromisoformat(response['updated_at']),
            reference=response.get('reference'),
            phone_number=response.get('phone_number'),
            metadata=response.get('metadata')
        )
        
        logger.info(f"Dépôt initié: {transaction.id}")
        return transaction
    
    def initiate_withdrawal(self, withdrawal_request: WithdrawalRequest) -> Transaction:
        """Initier un retrait d'argent"""
        withdrawal_request.validate()
        
        # Vérifier le solde avant le retrait
        balance = self.get_balance()
        if balance.get(withdrawal_request.currency.value, 0) < withdrawal_request.amount:
            raise InsufficientFundsError("Solde insuffisant pour ce retrait")
        
        payload = {
            'amount': withdrawal_request.amount,
            'currency': withdrawal_request.currency.value,
            'phone_number': withdrawal_request.phone_number,
            'account_number': withdrawal_request.account_number,
            'reason': withdrawal_request.reason,
            'metadata': withdrawal_request.metadata,
            'timestamp': int(time.time())
        }
        
        response = self._make_request('POST', '/withdrawals/initiate', data=payload)
        
        transaction = Transaction(
            id=response['transaction_id'],
            type='withdrawal',
            amount=response['amount'],
            currency=Currency(response['currency']),
            status=TransactionStatus(response['status']),
            created_at=datetime.fromisoformat(response['created_at']),
            updated_at=datetime.fromisoformat(response['updated_at']),
            phone_number=response.get('phone_number'),
            metadata=response.get('metadata')
        )
        
        logger.info(f"Retrait initié: {transaction.id}")
        return transaction
    
    def get_transaction_status(self, transaction_id: str, 
                              transaction_type: str = 'deposits') -> Transaction:
        """Obtenir le statut d'une transaction"""
        endpoint = f'/{transaction_type}/{transaction_id}/status'
        response = self._make_request('GET', endpoint)
        
        transaction = Transaction(
            id=response['transaction_id'],
            type=transaction_type.rstrip('s'),
            amount=response['amount'],
            currency=Currency(response['currency']),
            status=TransactionStatus(response['status']),
            created_at=datetime.fromisoformat(response['created_at']),
            updated_at=datetime.fromisoformat(response['updated_at']),
            reference=response.get('reference'),
            phone_number=response.get('phone_number'),
            error_message=response.get('error_message'),
            metadata=response.get('metadata')
        )
        
        return transaction
    
    def get_transactions(self, page: int = 1, limit: int = 50,
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> List[Transaction]:
        """Récupérer la liste des transactions"""
        params = {
            'page': page,
            'limit': limit
        }
        
        if start_date:
            params['start_date'] = start_date.isoformat()
        if end_date:
            params['end_date'] = end_date.isoformat()
        
        response = self._make_request('GET', '/transactions', params=params)
        
        transactions = []
        for tx_data in response.get('transactions', []):
            transaction = Transaction(
                id=tx_data['transaction_id'],
                type=tx_data['type'],
                amount=tx_data['amount'],
                currency=Currency(tx_data['currency']),
                status=TransactionStatus(tx_data['status']),
                created_at=datetime.fromisoformat(tx_data['created_at']),
                updated_at=datetime.fromisoformat(tx_data['updated_at']),
                reference=tx_data.get('reference'),
                phone_number=tx_data.get('phone_number'),
                error_message=tx_data.get('error_message'),
                metadata=tx_data.get('metadata')
            )
            transactions.append(transaction)
        
        return transactions
    
    def get_balance(self) -> Dict[str, float]:
        """Obtenir le solde du compte par devise"""
        response = self._make_request('GET', '/balance')
        return response.get('balances', {})
    
    def validate_webhook(self, signature: str, payload: str) -> bool:
        """Valider une notification webhook"""
        expected_signature = hmac.new(
            self.config.webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def wait_for_transaction_completion(self, transaction_id: str, 
                                       transaction_type: str = 'deposits',
                                       timeout: int = 300, 
                                       poll_interval: int = 5) -> Transaction:
        """Attendre la complétion d'une transaction avec polling"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            transaction = self.get_transaction_status(transaction_id, transaction_type)
            
            if transaction.status in [TransactionStatus.COMPLETED, 
                                     TransactionStatus.FAILED,
                                     TransactionStatus.CANCELLED]:
                return transaction
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Transaction {transaction_id} timeout après {timeout} secondes")
```

### Utilitaires (freemopay/utils.py)

```python
import re
import logging
from typing import Optional
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)

def validate_phone_number(phone_number: str, country_code: str = 'CM') -> bool:
    """Valider un numéro de téléphone selon le pays"""
    patterns = {
        'CM': r'^\+?237[6-9]\d{8}$',  # Cameroun
        'SN': r'^\+?221[7]\d{8}$',     # Sénégal
        'CI': r'^\+?225[0-9]\d{8}$',   # Côte d'Ivoire
    }
    
    pattern = patterns.get(country_code)
    if not pattern:
        logger.warning(f"Code pays non supporté: {country_code}")
        return False
    
    return bool(re.match(pattern, phone_number))

def format_amount(amount: float, currency: str = 'XAF') -> str:
    """Formater un montant selon la devise"""
    decimal_places = {
        'XAF': 0,  # Franc CFA n'a pas de centimes
        'EUR': 2,
        'USD': 2
    }
    
    places = decimal_places.get(currency, 2)
    decimal_amount = Decimal(str(amount))
    quantized = decimal_amount.quantize(Decimal(10) ** -places, rounding=ROUND_HALF_UP)
    
    return f"{quantized:,.{places}f} {currency}"

def generate_reference(prefix: str = 'TXN') -> str:
    """Générer une référence de transaction unique"""
    import uuid
    from datetime import datetime
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique_id = str(uuid.uuid4())[:8].upper()
    return f"{prefix}-{timestamp}-{unique_id}"

def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """Masquer les données sensibles pour les logs"""
    if len(data) <= visible_chars * 2:
        return '*' * len(data)
    
    return data[:visible_chars] + '*' * (len(data) - visible_chars * 2) + data[-visible_chars:]

class RateLimiter:
    """Limiteur de taux simple pour éviter de surcharger l'API"""
    
    def __init__(self, max_calls: int = 100, period: int = 60):
        self.max_calls = max_calls
        self.period = period
        self.calls = []
    
    def is_allowed(self) -> bool:
        """Vérifier si un appel est autorisé"""
        import time
        now = time.time()
        
        # Nettoyer les anciens appels
        self.calls = [call_time for call_time in self.calls 
                     if now - call_time < self.period]
        
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        
        return False
    
    def wait_if_needed(self):
        """Attendre si nécessaire avant le prochain appel"""
        import time
        while not self.is_allowed():
            time.sleep(1)
```

## Gestion des erreurs

### Gestionnaire d'erreurs centralisé

```python
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)

def handle_api_errors(func: Callable) -> Callable:
    """Décorateur pour gérer les erreurs API de manière uniforme"""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except AuthenticationError as e:
            logger.error(f"Erreur d'authentification: {str(e)}")
            # Réessayer l'authentification une fois
            if hasattr(args[0], 'authenticate'):
                args[0].authenticate()
                return func(*args, **kwargs)
            raise
        except ValidationError as e:
            logger.error(f"Erreur de validation: {str(e)}")
            raise
        except InsufficientFundsError as e:
            logger.error(f"Fonds insuffisants: {str(e)}")
            raise
        except RateLimitError as e:
            logger.warning(f"Limite de taux atteinte: {str(e)}")
            # Attendre avant de réessayer
            import time
            time.sleep(60)
            return func(*args, **kwargs)
        except NetworkError as e:
            logger.error(f"Erreur réseau: {str(e)}")
            raise
        except Exception as e:
            logger.critical(f"Erreur inattendue: {str(e)}", exc_info=True)
            raise FreeMoPayException(f"Erreur inattendue: {str(e)}")
    
    return wrapper
```

## Sécurité et bonnes pratiques

### Configuration de sécurité avancée

```python
import os
import secrets
from cryptography.fernet import Fernet
from typing import Optional

class SecurityManager:
    """Gestionnaire de sécurité pour les données sensibles"""
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        if encryption_key:
            self.cipher = Fernet(encryption_key)
        else:
            # Générer une clé si non fournie
            key = Fernet.generate_key()
            self.cipher = Fernet(key)
            logger.warning("Clé de chiffrement générée automatiquement. "
                         "Utilisez une clé persistante en production.")
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Chiffrer les données sensibles"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Déchiffrer les données sensibles"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Générer un token sécurisé"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Valider le format d'une clé API"""
        # Format attendu: 32 caractères alphanumériques
        import re
        pattern = r'^[a-zA-Z0-9]{32,}$'
        return bool(re.match(pattern, api_key))
    
    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """Nettoyer les entrées utilisateur"""
        import html
        # Échapper les caractères HTML
        sanitized = html.escape(input_str)
        # Supprimer les caractères de contrôle
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32)
        return sanitized.strip()

class AuditLogger:
    """Logger d'audit pour tracer toutes les opérations sensibles"""
    
    def __init__(self, log_file: str = 'audit.log'):
        self.logger = logging.getLogger('audit')
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_transaction(self, transaction_type: str, transaction_id: str,
                       amount: float, status: str, user_id: Optional[str] = None):
        """Logger une transaction"""
        self.logger.info(f"Transaction: type={transaction_type}, "
                        f"id={transaction_id}, amount={amount}, "
                        f"status={status}, user={user_id}")
    
    def log_authentication(self, success: bool, user_id: Optional[str] = None):
        """Logger une tentative d'authentification"""
        status = "SUCCESS" if success else "FAILURE"
        self.logger.info(f"Authentication: status={status}, user={user_id}")
    
    def log_error(self, error_type: str, error_message: str, 
                 transaction_id: Optional[str] = None):
        """Logger une erreur"""
        self.logger.error(f"Error: type={error_type}, message={error_message}, "
                         f"transaction={transaction_id}")
```

## Exemples d'utilisation

### Exemple complet d'intégration

```python
import asyncio
import logging
from datetime import datetime, timedelta
from freemopay.client import FreeMoPayClient
from freemopay.models import DepositRequest, WithdrawalRequest, Currency
from freemopay.exceptions import TransactionError, InsufficientFundsError
from config.settings import FreeMoPayConfig

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FreeMoPayService:
    """Service de haut niveau pour les opérations FreeMoPay"""
    
    def __init__(self):
        self.client = FreeMoPayClient()
        self.audit_logger = AuditLogger()
    
    def process_deposit(self, phone_number: str, amount: float, 
                       reference: Optional[str] = None) -> Dict:
        """Traiter un dépôt de bout en bout"""
        try:
            # Générer une référence si non fournie
            if not reference:
                reference = generate_reference('DEP')
            
            # Créer la demande de dépôt
            deposit_request = DepositRequest(
                amount=amount,
                currency=Currency.XAF,
                phone_number=phone_number,
                reference=reference,
                description=f"Dépôt de {format_amount(amount, 'XAF')}",
                metadata={
                    'timestamp': datetime.now().isoformat(),
                    'source': 'python_sdk'
                }
            )
            
            # Initier le dépôt
            logger.info(f"Initiation du dépôt: {reference}")
            transaction = self.client.initiate_deposit(deposit_request)
            
            # Logger pour l'audit
            self.audit_logger.log_transaction(
                'deposit', 
                transaction.id, 
                amount, 
                transaction.status.value
            )
            
            # Attendre la confirmation (avec timeout)
            logger.info(f"En attente de confirmation pour: {transaction.id}")
            final_transaction = self.client.wait_for_transaction_completion(
                transaction.id,
                'deposits',
                timeout=300
            )
            
            # Vérifier le statut final
            if final_transaction.status == TransactionStatus.COMPLETED:
                logger.info(f"Dépôt confirmé: {transaction.id}")
                return {
                    'success': True,
                    'transaction_id': transaction.id,
                    'amount': amount,
                    'status': 'completed',
                    'message': 'Dépôt effectué avec succès'
                }
            else:
                logger.error(f"Dépôt échoué: {transaction.id} - {final_transaction.error_message}")
                return {
                    'success': False,
                    'transaction_id': transaction.id,
                    'status': final_transaction.status.value,
                    'error': final_transaction.error_message
                }
                
        except Exception as e:
            logger.error(f"Erreur lors du dépôt: {str(e)}", exc_info=True)
            self.audit_logger.log_error('deposit_error', str(e))
            raise
    
    def process_withdrawal(self, phone_number: str, amount: float,
                         account_number: str) -> Dict:
        """Traiter un retrait de bout en bout"""
        try:
            # Vérifier le solde d'abord
            balance = self.client.get_balance()
            available_balance = balance.get('XAF', 0)
            
            if available_balance < amount:
                raise InsufficientFundsError(
                    f"Solde insuffisant. Disponible: {format_amount(available_balance, 'XAF')}"
                )
            
            # Créer la demande de retrait
            withdrawal_request = WithdrawalRequest(
                amount=amount,
                currency=Currency.XAF,
                phone_number=phone_number,
                account_number=account_number,
                reason="Retrait client",
                metadata={
                    'timestamp': datetime.now().isoformat(),
                    'source': 'python_sdk'
                }
            )
            
            # Initier le retrait
            logger.info(f"Initiation du retrait: {amount} XAF")
            transaction = self.client.initiate_withdrawal(withdrawal_request)
            
            # Logger pour l'audit
            self.audit_logger.log_transaction(
                'withdrawal',
                transaction.id,
                amount,
                transaction.status.value
            )
            
            # Attendre la confirmation
            final_transaction = self.client.wait_for_transaction_completion(
                transaction.id,
                'withdrawals',
                timeout=300
            )
            
            if final_transaction.status == TransactionStatus.COMPLETED:
                logger.info(f"Retrait confirmé: {transaction.id}")
                return {
                    'success': True,
                    'transaction_id': transaction.id,
                    'amount': amount,
                    'status': 'completed',
                    'message': 'Retrait effectué avec succès'
                }
            else:
                logger.error(f"Retrait échoué: {transaction.id}")
                return {
                    'success': False,
                    'transaction_id': transaction.id,
                    'status': final_transaction.status.value,
                    'error': final_transaction.error_message
                }
                
        except InsufficientFundsError as e:
            logger.warning(f"Fonds insuffisants pour le retrait: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Erreur lors du retrait: {str(e)}", exc_info=True)
            self.audit_logger.log_error('withdrawal_error', str(e))
            raise
    
    def get_transaction_history(self, days: int = 30) -> List[Dict]:
        """Récupérer l'historique des transactions"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            transactions = self.client.get_transactions(
                start_date=start_date,
                end_date=end_date,
                limit=100
            )
            
            return [
                {
                    'id': tx.id,
                    'type': tx.type,
                    'amount': tx.amount,
                    'currency': tx.currency.value,
                    'status': tx.status.value,
                    'date': tx.created_at.isoformat(),
                    'reference': tx.reference
                }
                for tx in transactions
            ]
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'historique: {str(e)}")
            raise
    
    def handle_webhook(self, headers: Dict, body: str) -> Dict:
        """Traiter une notification webhook"""
        try:
            # Valider la signature
            signature = headers.get('X-FreeMoPay-Signature')
            if not self.client.validate_webhook(signature, body):
                logger.warning("Signature webhook invalide")
                return {'status': 'error', 'message': 'Invalid signature'}
            
            # Parser le payload
            import json
            payload = json.loads(body)
            
            # Traiter selon le type d'événement
            event_type = payload.get('event_type')
            transaction_id = payload.get('transaction_id')
            
            logger.info(f"Webhook reçu: {event_type} pour {transaction_id}")
            
            if event_type == 'deposit.completed':
                # Traiter le dépôt complété
                self.on_deposit_completed(payload)
            elif event_type == 'withdrawal.completed':
                # Traiter le retrait complété
                self.on_withdrawal_completed(payload)
            elif event_type in ['deposit.failed', 'withdrawal.failed']:
                # Traiter l'échec
                self.on_transaction_failed(payload)
            
            return {'status': 'success', 'message': 'Webhook processed'}
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du webhook: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def on_deposit_completed(self, payload: Dict):
        """Callback pour dépôt complété"""
        transaction_id = payload.get('transaction_id')
        amount = payload.get('amount')
        logger.info(f"Dépôt complété: {transaction_id} - {amount}")
        # Implémenter la logique métier (mise à jour DB, notification, etc.)
    
    def on_withdrawal_completed(self, payload: Dict):
        """Callback pour retrait complété"""
        transaction_id = payload.get('transaction_id')
        amount = payload.get('amount')
        logger.info(f"Retrait complété: {transaction_id} - {amount}")
        # Implémenter la logique métier
    
    def on_transaction_failed(self, payload: Dict):
        """Callback pour transaction échouée"""
        transaction_id = payload.get('transaction_id')
        error = payload.get('error_message')
        logger.error(f"Transaction échouée: {transaction_id} - {error}")
        # Implémenter la logique de gestion d'erreur
```

### Script de test

```python
#!/usr/bin/env python3
"""
Script de test pour l'intégration FreeMoPay
"""

import sys
import logging
from freemopay_service import FreeMoPayService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_integration():
    """Tester l'intégration complète"""
    service = FreeMoPayService()
    
    try:
        # Test 1: Authentification
        logger.info("Test d'authentification...")
        service.client.authenticate()
        logger.info("✓ Authentification réussie")
        
        # Test 2: Vérification du solde
        logger.info("Vérification du solde...")
        balance = service.client.get_balance()
        logger.info(f"✓ Solde: {balance}")
        
        # Test 3: Dépôt test
        logger.info("Test de dépôt...")
        result = service.process_deposit(
            phone_number="+237690000000",
            amount=1000,
            reference="TEST-DEPOSIT-001"
        )
        if result['success']:
            logger.info(f"✓ Dépôt réussi: {result['transaction_id']}")
        else:
            logger.error(f"✗ Dépôt échoué: {result['error']}")
        
        # Test 4: Historique
        logger.info("Récupération de l'historique...")
        history = service.get_transaction_history(days=7)
        logger.info(f"✓ {len(history)} transactions trouvées")
        
        logger.info("\n=== Tests complétés avec succès ===")
        
    except Exception as e:
        logger.error(f"✗ Erreur lors des tests: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    test_integration()
```

## Configuration Docker

### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY . .

# Variables d'environnement par défaut
ENV PYTHONUNBUFFERED=1
ENV FREEMOPAY_ENVIRONMENT=sandbox

# Commande par défaut
CMD ["python", "-m", "freemopay_service"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  freemopay-integration:
    build: .
    environment:
      - FREEMOPAY_API_KEY=${FREEMOPAY_API_KEY}
      - FREEMOPAY_SECRET_KEY=${FREEMOPAY_SECRET_KEY}
      - FREEMOPAY_MERCHANT_ID=${FREEMOPAY_MERCHANT_ID}
      - FREEMOPAY_ENVIRONMENT=${FREEMOPAY_ENVIRONMENT:-sandbox}
      - FREEMOPAY_WEBHOOK_SECRET=${FREEMOPAY_WEBHOOK_SECRET}
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    ports:
      - "8000:8000"
    restart: unless-stopped
    networks:
      - freemopay-network

networks:
  freemopay-network:
    driver: bridge
```

## Tests unitaires

### tests/test_client.py

```python
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from freemopay.client import FreeMoPayClient
from freemopay.models import DepositRequest, Currency, TransactionStatus
from freemopay.exceptions import ValidationError, InsufficientFundsError

class TestFreeMoPayClient(unittest.TestCase):
    """Tests unitaires pour le client FreeMoPay"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.client = FreeMoPayClient()
        
    @patch('freemopay.client.requests.Session')
    def test_authentication(self, mock_session):
        """Test de l'authentification"""
        # Mock de la réponse
        mock_response = Mock()
        mock_response.json.return_value = {
            'access_token': 'test_token',
            'expires_in': 3600
        }
        mock_response.status_code = 200
        mock_session.return_value.request.return_value = mock_response
        
        # Test
        result = self.client.authenticate()
        
        # Vérifications
        self.assertEqual(self.client.access_token, 'test_token')
        self.assertIsNotNone(self.client.token_expiry)
    
    def test_deposit_validation(self):
        """Test de la validation des dépôts"""
        # Test avec montant négatif
        with self.assertRaises(ValidationError):
            deposit = DepositRequest(
                amount=-100,
                currency=Currency.XAF,
                phone_number="+237690000000",
                reference="TEST"
            )
            deposit.validate()
        
        # Test avec numéro manquant
        with self.assertRaises(ValidationError):
            deposit = DepositRequest(
                amount=1000,
                currency=Currency.XAF,
                phone_number="",
                reference="TEST"
            )
            deposit.validate()
    
    @patch.object(FreeMoPayClient, '_make_request')
    def test_initiate_deposit(self, mock_request):
        """Test de l'initiation d'un dépôt"""
        # Mock de la réponse
        mock_request.return_value = {
            'transaction_id': 'TXN123',
            'amount': 1000,
            'currency': 'XAF',
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Créer une demande de dépôt
        deposit = DepositRequest(
            amount=1000,
            currency=Currency.XAF,
            phone_number="+237690000000",
            reference="TEST"
        )
        
        # Test
        transaction = self.client.initiate_deposit(deposit)
        
        # Vérifications
        self.assertEqual(transaction.id, 'TXN123')
        self.assertEqual(transaction.amount, 1000)
        self.assertEqual(transaction.status, TransactionStatus.PENDING)
    
    @patch.object(FreeMoPayClient, 'get_balance')
    def test_insufficient_funds(self, mock_balance):
        """Test de la gestion des fonds insuffisants"""
        # Mock du solde
        mock_balance.return_value = {'XAF': 500}
        
        # Test
        withdrawal = WithdrawalRequest(
            amount=1000,
            currency=Currency.XAF,
            phone_number="+237690000000",
            account_number="ACC123"
        )
        
        with self.assertRaises(InsufficientFundsError):
            self.client.initiate_withdrawal(withdrawal)

if __name__ == '__main__':
    unittest.main()
```

## Monitoring et observabilité

### Configuration de logging avancé

```python
import logging
import json
from pythonjsonlogger import jsonlogger

def setup_logging(log_level=logging.INFO):
    """Configurer le logging structuré"""
    
    # Formateur JSON pour les logs structurés
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logHandler.setFormatter(formatter)
    
    # Configuration du logger racine
    logger = logging.getLogger()
    logger.addHandler(logHandler)
    logger.setLevel(log_level)
    
    # Logger spécifique pour les métriques
    metrics_logger = logging.getLogger('metrics')
    metrics_handler = logging.FileHandler('metrics.log')
    metrics_handler.setFormatter(formatter)
    metrics_logger.addHandler(metrics_handler)
    
    return logger

class MetricsCollector:
    """Collecteur de métriques pour le monitoring"""
    
    def __init__(self):
        self.logger = logging.getLogger('metrics')
        self.metrics = {
            'transactions_total': 0,
            'transactions_success': 0,
            'transactions_failed': 0,
            'api_calls_total': 0,
            'api_errors_total': 0
        }
    
    def increment(self, metric: str, value: int = 1):
        """Incrémenter une métrique"""
        if metric in self.metrics:
            self.metrics[metric] += value
            self.logger.info(json.dumps({
                'metric': metric,
                'value': self.metrics[metric],
                'timestamp': datetime.now().isoformat()
            }))
    
    def record_transaction(self, transaction_type: str, status: str, 
                          duration: float, amount: float):
        """Enregistrer les métriques d'une transaction"""
        self.logger.info(json.dumps({
            'event': 'transaction',
            'type': transaction_type,
            'status': status,
            'duration_ms': duration * 1000,
            'amount': amount,
            'timestamp': datetime.now().isoformat()
        }))
    
    def get_metrics(self) -> Dict:
        """Obtenir toutes les métriques"""
        return self.metrics.copy()
```

## Conclusion

Cette documentation fournit une base solide pour l'intégration de l'API FreeMoPay en Python. Les points clés incluent:

1. **Architecture modulaire** permettant une maintenance facile
2. **Gestion robuste des erreurs** avec retry automatique
3. **Sécurité renforcée** avec chiffrement et validation
4. **Logging et monitoring** pour la production
5. **Tests unitaires** pour assurer la qualité
6. **Documentation complète** des endpoints et paramètres

Pour obtenir l'accès à l'API FreeMoPay réelle, contactez leur équipe commerciale via business.freemopay.com pour établir un partenariat et obtenir les credentials nécessaires.