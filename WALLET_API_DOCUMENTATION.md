# Documentation API Wallet - Woila Backend

## 📋 Vue d'ensemble

Cette documentation présente les APIs de gestion de portefeuille électronique (wallet) pour l'application Woila. Les utilisateurs (chauffeurs et clients) peuvent déposer, retirer de l'argent et consulter l'historique de leurs transactions.

## 🔐 Authentification

Toutes les APIs nécessitent une authentification via un token Bearer dans l'en-tête Authorization :

```
Authorization: Bearer <votre_token>
```

Le token est obtenu via l'API de connexion `/api/auth/login/`.

## 📊 APIs Disponibles

### 1. 💰 Obtenir le solde du wallet

**Endpoint :** `GET /api/wallet/balance/`

**Description :** Récupère le solde actuel du portefeuille de l'utilisateur connecté.

**Headers requis :**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Réponse de succès (200) :**
```json
{
    "success": true,
    "balance": 15000.00,
    "user_type": "driver",
    "user_id": 1
}
```

**Réponse d'erreur (401) :**
```json
{
    "success": false,
    "message": "Token invalide"
}
```

---

### 2. 📥 Dépôt d'argent

**Endpoint :** `POST /api/wallet/deposit/`

**Description :** Initie un dépôt d'argent dans le portefeuille via Mobile Money (FreeMoPay).

**Headers requis :**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Corps de la requête :**
```json
{
    "amount": 10000,
    "phone_number": "+237690000000",
    "description": "Rechargement wallet" // Optionnel
}
```

**Paramètres :**
- `amount` (number, requis) : Montant à déposer en FCFA (> 0)
- `phone_number` (string, requis) : Numéro de téléphone Mobile Money
- `description` (string, optionnel) : Description du dépôt

**Réponse de succès (200) :**
```json
{
    "success": true,
    "transaction_reference": "DEP-20231201123045-A1B2C3D4",
    "freemopay_reference": "FM123456789",
    "amount": 10000,
    "status": "completed",
    "message": "Dépôt initié avec succès",
    "final_result": {
        "status": "SUCCESS",
        "final_status": "SUCCESS",
        "reason": "Payment completed",
        "polling_duration": 45.2,
        "attempts": 23,
        "reference": "FM123456789",
        "full_response": {...}
    }
}
```

**Réponse d'erreur (400) :**
```json
{
    "success": false,
    "transaction_reference": "DEP-20231201123045-A1B2C3D4",
    "message": "Erreur lors de l'initiation du paiement",
    "error": {
        "status": "FAILED",
        "message": "Numéro de téléphone invalide"
    }
}
```

**Status possibles :**
- `completed` : Dépôt réussi et wallet crédité
- `failed` : Dépôt échoué
- `processing` : En cours de traitement
- `timeout` : Timeout du polling FreeMoPay

---

### 3. 📤 Retrait d'argent

**Endpoint :** `POST /api/wallet/withdrawal/`

**Description :** Initie un retrait d'argent du portefeuille vers Mobile Money.

**Headers requis :**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Corps de la requête :**
```json
{
    "amount": 5000,
    "phone_number": "+237690000000",
    "description": "Retrait vers Mobile Money" // Optionnel
}
```

**Paramètres :**
- `amount` (number, requis) : Montant à retirer en FCFA (> 0, ≤ solde disponible)
- `phone_number` (string, requis) : Numéro Mobile Money pour recevoir l'argent
- `description` (string, optionnel) : Description du retrait

**Réponse de succès (200) :**
```json
{
    "success": true,
    "transaction_reference": "WIT-20231201123045-B5C6D7E8",
    "amount": 5000,
    "status": "completed",
    "message": "Retrait effectué avec succès",
    "new_balance": 10000.00
}
```

**Réponse d'erreur (400) - Solde insuffisant :**
```json
{
    "success": false,
    "message": "Solde insuffisant. Solde disponible: 3000.00 FCFA"
}
```

---

### 4. 📋 Historique des transactions

**Endpoint :** `GET /api/wallet/transactions/`

**Description :** Récupère l'historique paginé des transactions du portefeuille.

**Headers requis :**
```
Authorization: Bearer <token>
```

**Paramètres de requête (optionnels) :**
- `page` (int) : Numéro de page (défaut: 1)
- `page_size` (int) : Nombre d'éléments par page (défaut: 20, max: 100)
- `type` (string) : Type de transaction (`deposit`, `withdrawal`, `transfer_in`, `transfer_out`, `refund`, `payment`)

**Exemple d'URL :**
```
GET /api/wallet/transactions/?page=1&page_size=10&type=deposit
```

**Réponse de succès (200) :**
```json
{
    "success": true,
    "transactions": [
        {
            "id": 1,
            "reference": "DEP-20231201123045-A1B2C3D4",
            "type": "deposit",
            "type_display": "Dépôt",
            "amount": 10000.0,
            "status": "completed",
            "status_display": "Complété",
            "payment_method": "mobile_money",
            "phone_number": "+237690000000",
            "description": "Dépôt de 10000 FCFA",
            "balance_before": 5000.0,
            "balance_after": 15000.0,
            "created_at": "2023-12-01T12:30:45.123456Z",
            "completed_at": "2023-12-01T12:32:15.789012Z",
            "error_message": null
        },
        {
            "id": 2,
            "reference": "WIT-20231201140030-C9D8E7F6",
            "type": "withdrawal",
            "type_display": "Retrait",
            "amount": 2000.0,
            "status": "completed",
            "status_display": "Complété",
            "payment_method": "mobile_money",
            "phone_number": "+237690000000",
            "description": "Retrait de 2000 FCFA",
            "balance_before": 15000.0,
            "balance_after": 13000.0,
            "created_at": "2023-12-01T14:00:30.456789Z",
            "completed_at": "2023-12-01T14:00:35.123456Z",
            "error_message": null
        }
    ],
    "pagination": {
        "page": 1,
        "page_size": 20,
        "total_count": 2,
        "total_pages": 1
    },
    "current_balance": 13000.0
}
```

---

### 5. 🔍 Détails d'une transaction

**Endpoint :** `GET /api/wallet/transactions/{reference}/`

**Description :** Récupère les détails complets d'une transaction spécifique.

**Headers requis :**
```
Authorization: Bearer <token>
```

**Paramètres d'URL :**
- `reference` (string) : Référence unique de la transaction

**Exemple d'URL :**
```
GET /api/wallet/transactions/DEP-20231201123045-A1B2C3D4/
```

**Réponse de succès (200) :**
```json
{
    "success": true,
    "transaction": {
        "id": 1,
        "reference": "DEP-20231201123045-A1B2C3D4",
        "type": "deposit",
        "type_display": "Dépôt",
        "amount": 10000.0,
        "status": "completed",
        "status_display": "Complété",
        "payment_method": "mobile_money",
        "phone_number": "+237690000000",
        "description": "Dépôt de 10000 FCFA",
        "balance_before": 5000.0,
        "balance_after": 15000.0,
        "freemopay_reference": "FM123456789",
        "freemopay_external_id": "DEP-20231201123045-A1B2C3D4",
        "created_at": "2023-12-01T12:30:45.123456Z",
        "updated_at": "2023-12-01T12:32:15.789012Z",
        "completed_at": "2023-12-01T12:32:15.789012Z",
        "error_message": null,
        "metadata": {
            "user_type": "driver",
            "phone_number": "+237690000000",
            "initiated_at": "2023-12-01T12:30:45.123456Z",
            "freemopay_polling_result": {
                "status": "SUCCESS",
                "final_status": "SUCCESS",
                "reason": "Payment completed",
                "polling_duration": 45.2,
                "attempts": 23
            },
            "completed_at": "2023-12-01T12:32:15.789012Z"
        }
    }
}
```

**Réponse d'erreur (404) :**
```json
{
    "success": false,
    "message": "Transaction non trouvée"
}
```

---

## 🔄 Flux de transaction

### Dépôt d'argent :

1. **Initiation** : L'utilisateur appelle `/api/wallet/deposit/` avec le montant et numéro de téléphone
2. **Création** : Une transaction est créée avec le statut `pending`
3. **FreeMoPay** : Appel à l'API FreeMoPay pour initier le paiement
4. **Polling** : Vérification du statut toutes les 2 secondes pendant max 2 minutes
5. **Finalisation** : 
   - Si succès : Wallet crédité, statut `completed`
   - Si échec : Statut `failed` avec message d'erreur
   - Si timeout : Statut `failed` avec message de timeout

### Retrait d'argent :

1. **Vérification** : Contrôle du solde disponible
2. **Blocage** : Débit temporaire du montant du wallet
3. **Traitement** : Simulation du traitement (5 secondes)
4. **Finalisation** : Statut `completed` ou remise du montant en cas d'erreur

---

## 🏷️ Types de transactions

| Type | Description |
|------|-------------|
| `deposit` | Dépôt d'argent depuis Mobile Money |
| `withdrawal` | Retrait d'argent vers Mobile Money |
| `transfer_in` | Transfert entrant (d'un autre utilisateur) |
| `transfer_out` | Transfert sortant (vers un autre utilisateur) |
| `refund` | Remboursement |
| `payment` | Paiement (pour une course, etc.) |

## 📊 Statuts de transaction

| Statut | Description |
|--------|-------------|
| `pending` | En attente de traitement |
| `processing` | En cours de traitement |
| `completed` | Complétée avec succès |
| `failed` | Échouée |
| `cancelled` | Annulée |

## 🎯 Méthodes de paiement

| Méthode | Description |
|---------|-------------|
| `mobile_money` | Mobile Money (MTN, Orange, etc.) |
| `bank_transfer` | Virement bancaire |
| `cash` | Espèces |
| `other` | Autre méthode |

---

## 🚀 Exemples d'utilisation

### Exemple complet en JavaScript (Frontend)

```javascript
// Configuration de base
const API_BASE = 'https://your-domain.com/api';
const token = localStorage.getItem('authToken');

const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
};

// 1. Obtenir le solde
async function getBalance() {
    try {
        const response = await fetch(`${API_BASE}/wallet/balance/`, {
            method: 'GET',
            headers: headers
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log(`Solde actuel: ${data.balance} FCFA`);
            return data.balance;
        } else {
            console.error('Erreur:', data.message);
        }
    } catch (error) {
        console.error('Erreur réseau:', error);
    }
}

// 2. Effectuer un dépôt
async function makeDeposit(amount, phoneNumber, description = '') {
    try {
        const response = await fetch(`${API_BASE}/wallet/deposit/`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                amount: amount,
                phone_number: phoneNumber,
                description: description
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('Dépôt réussi:', data);
            console.log(`Référence: ${data.transaction_reference}`);
            console.log(`Statut: ${data.status}`);
            return data;
        } else {
            console.error('Dépôt échoué:', data.message);
            throw new Error(data.message);
        }
    } catch (error) {
        console.error('Erreur lors du dépôt:', error);
        throw error;
    }
}

// 3. Effectuer un retrait
async function makeWithdrawal(amount, phoneNumber, description = '') {
    try {
        const response = await fetch(`${API_BASE}/wallet/withdrawal/`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                amount: amount,
                phone_number: phoneNumber,
                description: description
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('Retrait réussi:', data);
            console.log(`Nouveau solde: ${data.new_balance} FCFA`);
            return data;
        } else {
            console.error('Retrait échoué:', data.message);
            throw new Error(data.message);
        }
    } catch (error) {
        console.error('Erreur lors du retrait:', error);
        throw error;
    }
}

// 4. Obtenir l'historique des transactions
async function getTransactionHistory(page = 1, pageSize = 20, type = null) {
    try {
        let url = `${API_BASE}/wallet/transactions/?page=${page}&page_size=${pageSize}`;
        if (type) {
            url += `&type=${type}`;
        }
        
        const response = await fetch(url, {
            method: 'GET',
            headers: headers
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log(`${data.transactions.length} transactions trouvées`);
            console.log(`Solde actuel: ${data.current_balance} FCFA`);
            return data;
        } else {
            console.error('Erreur:', data.message);
        }
    } catch (error) {
        console.error('Erreur réseau:', error);
    }
}

// 5. Obtenir les détails d'une transaction
async function getTransactionDetails(reference) {
    try {
        const response = await fetch(`${API_BASE}/wallet/transactions/${reference}/`, {
            method: 'GET',
            headers: headers
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('Détails de la transaction:', data.transaction);
            return data.transaction;
        } else {
            console.error('Transaction non trouvée:', data.message);
        }
    } catch (error) {
        console.error('Erreur réseau:', error);
    }
}

// Exemple d'utilisation
async function example() {
    try {
        // Vérifier le solde avant
        const initialBalance = await getBalance();
        
        // Effectuer un dépôt de 10,000 FCFA
        const depositResult = await makeDeposit(10000, '+237690000000', 'Test de dépôt');
        
        // Vérifier le nouveau solde
        const newBalance = await getBalance();
        
        // Obtenir l'historique
        const history = await getTransactionHistory(1, 10);
        
        // Obtenir les détails de la dernière transaction
        if (history.transactions.length > 0) {
            const lastTransaction = history.transactions[0];
            const details = await getTransactionDetails(lastTransaction.reference);
        }
        
    } catch (error) {
        console.error('Erreur dans l\'exemple:', error);
    }
}
```

### Exemple en Python

```python
import requests
import json

class WalletAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def get_balance(self):
        """Obtenir le solde du wallet"""
        response = requests.get(
            f'{self.base_url}/wallet/balance/',
            headers=self.headers
        )
        return response.json()
    
    def make_deposit(self, amount, phone_number, description=''):
        """Effectuer un dépôt"""
        data = {
            'amount': amount,
            'phone_number': phone_number,
            'description': description
        }
        response = requests.post(
            f'{self.base_url}/wallet/deposit/',
            headers=self.headers,
            json=data
        )
        return response.json()
    
    def make_withdrawal(self, amount, phone_number, description=''):
        """Effectuer un retrait"""
        data = {
            'amount': amount,
            'phone_number': phone_number,
            'description': description
        }
        response = requests.post(
            f'{self.base_url}/wallet/withdrawal/',
            headers=self.headers,
            json=data
        )
        return response.json()
    
    def get_transaction_history(self, page=1, page_size=20, transaction_type=None):
        """Obtenir l'historique des transactions"""
        params = {
            'page': page,
            'page_size': page_size
        }
        if transaction_type:
            params['type'] = transaction_type
            
        response = requests.get(
            f'{self.base_url}/wallet/transactions/',
            headers=self.headers,
            params=params
        )
        return response.json()
    
    def get_transaction_details(self, reference):
        """Obtenir les détails d'une transaction"""
        response = requests.get(
            f'{self.base_url}/wallet/transactions/{reference}/',
            headers=self.headers
        )
        return response.json()

# Utilisation
api = WalletAPI('https://your-domain.com/api', 'your_token_here')

# Obtenir le solde
balance = api.get_balance()
print(f"Solde: {balance['balance']} FCFA")

# Effectuer un dépôt
deposit = api.make_deposit(10000, '+237690000000', 'Test de dépôt')
if deposit['success']:
    print(f"Dépôt réussi: {deposit['transaction_reference']}")
else:
    print(f"Dépôt échoué: {deposit['message']}")
```

---

## ⚠️ Gestion des erreurs

Les APIs retournent toujours un objet JSON avec un champ `success` :

- `success: true` : Opération réussie
- `success: false` : Erreur, voir le champ `message` pour les détails

### Codes d'erreur HTTP courrants :

- **200** : Succès
- **400** : Données invalides (montant négatif, téléphone manquant, etc.)
- **401** : Non authentifié (token invalide ou manquant)
- **404** : Ressource non trouvée (transaction inexistante)
- **500** : Erreur interne du serveur

---

## 🔒 Sécurité

1. **Authentification** : Toutes les APIs nécessitent un token valide
2. **Validation** : Tous les montants sont validés côté serveur
3. **Transactions atomiques** : Les opérations de wallet utilisent les transactions de base de données
4. **Audit** : Toutes les transactions sont loggées avec des détails complets
5. **Solde négatif** : Impossible d'avoir un solde négatif (vérification avant retrait)

---

## 🧪 Tests et développement

### Variables d'environnement recommandées pour les tests :

```env
# FreeMoPay Configuration (Sandbox)
FREEMOPAY_APP_KEY=your_test_app_key
FREEMOPAY_SECRET_KEY=your_test_secret_key
FREEMOPAY_BASE_URL=https://api-test.freemopay.com/api/v2

# Database (pour les tests)
DATABASE_URL=sqlite:///test_db.sqlite3

# Logging
LOG_LEVEL=DEBUG
```

### Numéros de test FreeMoPay :

- **+237690000001** : Paiement toujours réussi
- **+237690000002** : Paiement toujours échoué
- **+237690000003** : Paiement avec timeout

---

## 📝 Notes importantes

1. **Polling FreeMoPay** : Le système attend max 2 minutes pour la confirmation de paiement
2. **Retraits** : Actuellement simulés (5 secondes), en attente d'une vraie API de retrait
3. **Devises** : Seul le FCFA est supporté pour le moment
4. **Limites** : Aucune limite de montant imposée par l'API (à définir selon les besoins métier)
5. **Concurrence** : Les opérations de wallet utilisent des verrous de base de données pour éviter les conditions de course

---

## 🆔 Identifiants de référence

Les références de transaction suivent ce format :
```
{TYPE}-{TIMESTAMP}-{UUID_8_CHARS}
```

Exemples :
- `DEP-20231201123045-A1B2C3D4` (Dépôt)
- `WIT-20231201140030-B5C6D7E8` (Retrait)
- `TRA-20231201150030-C7D8E9F0` (Transfert)

Ces références sont uniques et permettent un suivi facile des transactions.