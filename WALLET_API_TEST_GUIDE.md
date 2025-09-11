# 🧪 Guide de Test des APIs Wallet - Woila

## 🚀 Démarrage rapide

### 1. Démarrer le serveur
```bash
cd /Users/macbookpro/Desktop/Developments/Personnals/Woila/woila_backend
python manage.py runserver
```

### 2. Accéder à la documentation Swagger
Ouvrez votre navigateur : `http://localhost:8000/api/docs/swagger/`

## 🔐 Étapes d'authentification

### 1. Se connecter (via API de login - non documentée dans Swagger)
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+237690000000",
    "password": "votre_mot_de_passe", 
    "user_type": "driver"
  }'
```

**Réponse attendue :**
```json
{
  "success": true,
  "token": "abc123def456ghi789...",
  "user_type": "driver",
  "user_id": 1
}
```

### 2. Configurer l'authentification dans Swagger
1. Cliquez sur le bouton **"Authorize"** 🔒 en haut à droite
2. Entrez : `Bearer abc123def456ghi789...` (remplacez par votre token)
3. Cliquez sur **"Authorize"**
4. Fermez la fenêtre

## 🧪 Tests étape par étape

### Test 1 : Consulter le solde 💰

**API :** `GET /api/v1/wallet/balance/`

1. Dans Swagger, trouvez l'endpoint "💰 Consulter le solde"
2. Cliquez sur **"Try it out"**
3. Cliquez sur **"Execute"**

**Résultat attendu :**
```json
{
  "success": true,
  "balance": 0.00,
  "user_type": "driver", 
  "user_id": 1
}
```

### Test 2 : Effectuer un dépôt 📥

**API :** `POST /api/v1/wallet/deposit/`

1. Trouvez l'endpoint "📥 Déposer de l'argent"
2. Cliquez sur **"Try it out"**
3. Modifiez le JSON de requête :
```json
{
  "amount": 10000,
  "phone_number": "+237690000001",
  "description": "Test de dépôt"
}
```
4. Cliquez sur **"Execute"**

**Résultat attendu (si FreeMoPay configuré) :**
```json
{
  "success": true,
  "transaction_reference": "DEP-20231201123045-A1B2C3D4",
  "freemopay_reference": "FM123456789",
  "amount": 10000,
  "status": "completed",
  "message": "Dépôt initié avec succès"
}
```

### Test 3 : Vérifier le nouveau solde 💰

Répétez le Test 1 - le solde devrait maintenant être de 10,000 FCFA.

### Test 4 : Effectuer un retrait 📤

**API :** `POST /api/v1/wallet/withdrawal/`

1. Trouvez l'endpoint "📤 Retirer de l'argent"
2. Cliquez sur **"Try it out"**
3. Modifiez le JSON :
```json
{
  "amount": 3000,
  "phone_number": "+237690000001",
  "description": "Test de retrait"
}
```
4. Cliquez sur **"Execute"**

**Résultat attendu :**
```json
{
  "success": true,
  "transaction_reference": "WIT-20231201140030-B5C6D7E8",
  "amount": 3000,
  "status": "completed",
  "message": "Retrait effectué avec succès",
  "new_balance": 7000.00
}
```

### Test 5 : Consulter l'historique 📋

**API :** `GET /api/v1/wallet/transactions/`

1. Trouvez l'endpoint "📋 Historique des transactions"
2. Cliquez sur **"Try it out"**
3. Laissez les paramètres par défaut ou modifiez :
   - `page`: 1
   - `page_size`: 20
   - `type`: (laissez vide pour tout voir)
4. Cliquez sur **"Execute"**

**Résultat attendu :**
```json
{
  "success": true,
  "transactions": [
    {
      "id": 2,
      "reference": "WIT-20231201140030-B5C6D7E8",
      "type": "withdrawal",
      "type_display": "Retrait",
      "amount": 3000.0,
      "status": "completed",
      // ... autres champs
    },
    {
      "id": 1, 
      "reference": "DEP-20231201123045-A1B2C3D4",
      "type": "deposit",
      "type_display": "Dépôt",
      "amount": 10000.0,
      "status": "completed",
      // ... autres champs
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_count": 2,
    "total_pages": 1
  },
  "current_balance": 7000.0
}
```

### Test 6 : Détails d'une transaction 🔍

**API :** `GET /api/v1/wallet/transactions/{reference}/`

1. Trouvez l'endpoint "🔍 Détails d'une transaction"
2. Cliquez sur **"Try it out"**
3. Remplacez `{reference}` par une vraie référence (ex: `DEP-20231201123045-A1B2C3D4`)
4. Cliquez sur **"Execute"**

## 🚫 Tests d'erreurs

### Test d'erreur 1 : Retrait avec solde insuffisant
```json
{
  "amount": 50000,
  "phone_number": "+237690000001",
  "description": "Test solde insuffisant"
}
```

**Résultat attendu :**
```json
{
  "success": false,
  "message": "Solde insuffisant. Solde disponible: 7000.00 FCFA"
}
```

### Test d'erreur 2 : Montant invalide
```json
{
  "amount": -1000,
  "phone_number": "+237690000001"
}
```

**Résultat attendu :**
```json
{
  "success": false,
  "message": "Le montant doit être supérieur à 0"
}
```

### Test d'erreur 3 : Numéro de téléphone manquant
```json
{
  "amount": 1000,
  "phone_number": ""
}
```

**Résultat attendu :**
```json
{
  "success": false,
  "message": "Le numéro de téléphone est requis"
}
```

## 📝 Tests avec cURL (Alternative)

Si vous préférez tester avec cURL :

```bash
# Token à remplacer
TOKEN="votre_token_ici"

# 1. Solde
curl -X GET "http://localhost:8000/api/v1/wallet/balance/" \
  -H "Authorization: Bearer $TOKEN"

# 2. Dépôt
curl -X POST "http://localhost:8000/api/v1/wallet/deposit/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 10000,
    "phone_number": "+237690000001",
    "description": "Test cURL"
  }'

# 3. Retrait
curl -X POST "http://localhost:8000/api/v1/wallet/withdrawal/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 2000,
    "phone_number": "+237690000001",
    "description": "Test retrait cURL"
  }'

# 4. Historique
curl -X GET "http://localhost:8000/api/v1/wallet/transactions/?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"

# 5. Détails transaction (remplacer REFERENCE)
curl -X GET "http://localhost:8000/api/v1/wallet/transactions/DEP-20231201123045-A1B2C3D4/" \
  -H "Authorization: Bearer $TOKEN"
```

## 🔧 Configuration FreeMoPay pour les tests

Pour que les dépôts fonctionnent réellement, assurez-vous que le fichier `/api/services/freemopay.py` a les bonnes clés :

```python
# Dans api/services/freemopay.py
APP_KEY = "votre_vraie_app_key"  
SECRET_KEY = "votre_vraie_secret_key"
BASE_URL = "https://api-v2.freemopay.com/api/v2"  # ou sandbox
```

## 🐛 Dépannage

### Erreur 401 "Token invalide"
- Vérifiez que le token n'a pas expiré
- Reconnectez-vous via `/api/v1/auth/login/`
- Vérifiez le format : `Bearer <token>`

### Erreur 500 "Erreur interne"
- Vérifiez les logs Django dans la console
- Vérifiez que la base de données est migrée : `python manage.py migrate`

### FreeMoPay ne fonctionne pas
- Vérifiez les clés API dans `freemopay.py`
- Testez d'abord avec des numéros de test FreeMoPay
- Vérifiez les logs pour voir les réponses de l'API

## 📊 Numéros de test FreeMoPay

Si vous avez accès au sandbox FreeMoPay :

- `+237690000001` : Paiement toujours réussi
- `+237690000002` : Paiement toujours échoué  
- `+237690000003` : Paiement avec timeout

## ✅ Checklist de tests

- [ ] Authentification réussie
- [ ] Consultation du solde initial
- [ ] Dépôt d'argent réussi
- [ ] Vérification du nouveau solde
- [ ] Retrait d'argent réussi
- [ ] Historique des transactions
- [ ] Détails d'une transaction
- [ ] Test d'erreur : solde insuffisant
- [ ] Test d'erreur : montant invalide
- [ ] Test d'erreur : numéro manquant
- [ ] Pagination de l'historique
- [ ] Filtrage par type de transaction

## 🎯 Scénarios de test avancés

### Scénario 1 : Utilisateur complet
1. Nouveau solde (0 FCFA)
2. Dépôt de 50,000 FCFA
3. Plusieurs retraits (10,000, 5,000, 15,000)
4. Consultation historique complet
5. Vérification solde final (20,000 FCFA)

### Scénario 2 : Gestion d'erreurs
1. Tentative retrait > solde
2. Montants négatifs
3. Numéros invalides
4. Transactions inexistantes

### Scénario 3 : Pagination
1. Créer 25 transactions
2. Tester pagination avec `page_size=10`
3. Parcourir toutes les pages
4. Filtrer par type

Bonne chance avec vos tests ! 🚀