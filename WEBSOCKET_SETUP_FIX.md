# Fix WebSocket 404 + Redis Errors 🔧

## ❌ **Problèmes identifiés dans les logs :**

```
ERROR: Error 61 connecting to 127.0.0.1:6379. Connect call failed
WARNING: Not Found: /ws/driver/28/
```

## ✅ **Solutions appliquées :**

### **1. Fix Redis/Channels Layer**

**Avant :**
```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',  # ❌ Nécessite Redis
        'CONFIG': {"hosts": [('127.0.0.1', 6379)]},
    },
}
```

**Après :**
```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',  # ✅ Pas besoin de Redis
    },
}
```

### **2. Fix Serveur WebSocket**

**❌ Problème :** Vous utilisez `python manage.py runserver` qui **NE SUPPORTE PAS** les WebSockets

**✅ Solution :** Utiliser **Daphne** (serveur ASGI)

## 🚀 **Comment redémarrer correctement :**

### **Option 1: Script automatique**
```bash
cd woila_backend/
./start_server.sh
```

### **Option 2: Commande manuelle**
```bash
cd woila_backend/
pip install daphne  # Si pas installé
daphne -b 0.0.0.0 -p 8001 woila_backend.asgi:application
```

### **Option 3: Avec logs détaillés**
```bash
daphne -b 0.0.0.0 -p 8001 -v 2 woila_backend.asgi:application
```

## 📡 **Vérification que ça marche :**

### **1. Logs attendus (plus d'erreurs) :**
```
INFO: Application startup complete.
INFO: Listening on http://0.0.0.0:8001
✅ WebSocket connected successfully  # Au lieu de 404
📡 Diffusion GPS démarrée pour le chauffeur 28  # Au lieu d'erreur Redis
```

### **2. Test WebSocket**
```bash
# Tester la connexion WebSocket avec curl
wscat -c "ws://localhost:8001/ws/driver/28/"
```

### **3. Test depuis Flutter**
L'app Flutter devrait maintenant se connecter sans erreur 404.

## 🔧 **Fichiers modifiés :**

1. **`woila_backend/settings.py`** - Channel Layer → InMemory
2. **`start_server.sh`** - Script de démarrage avec Daphne
3. **`WEBSOCKET_SETUP_FIX.md`** - Ce guide

## ⚠️ **Notes importantes :**

### **Développement vs Production**

**Développement (actuel) :**
- ✅ `InMemoryChannelLayer` - Simple, pas de dépendances
- ⚠️ Limité à un seul processus server

**Production (futur) :**
- 🔧 `RedisChannelLayer` - Multi-processus, scalable  
- 📋 Nécessite Redis: `brew install redis` ou `apt install redis-server`

### **URLs WebSocket après fix :**
- **Driver:** `ws://192.168.1.185:8001/ws/driver/28/`
- **Customer:** `ws://192.168.1.185:8001/ws/customer/1/`

### **Tests fonctionnels**
Après redémarrage avec Daphne, tous ces éléments devraient fonctionner :
- ✅ Connexion WebSocket sans 404
- ✅ Diffusion GPS automatique sans erreur Redis  
- ✅ Messages `location_broadcasting_started`
- ✅ Position diffusée toutes les 5 secondes
- ✅ App Flutter reçoit les confirmations GPS

## 🎉 **Résultat final**

```bash
cd woila_backend/
./start_server.sh
```

**Plus d'erreurs Redis ❌ → GPS fonctionne ✅**  
**Plus de 404 WebSocket ❌ → Connexions réussies ✅**