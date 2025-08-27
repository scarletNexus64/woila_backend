# Commandes pour démarrer le serveur WebSocket 🚀

## ✅ **Méthode recommandée (étape par étape) :**

```bash
# 1. Aller dans le dossier backend
cd /Users/macbookpro/Desktop/Developments/Personnals/Woila/woila_backend

# 2. Activer l'environnement virtuel
source venv/bin/activate

# 3. Installer Daphne si nécessaire
pip install daphne

# 4. Définir les variables d'environnement Django
export DJANGO_SETTINGS_MODULE=woila_backend.settings

# 5. Démarrer le serveur avec Daphne
daphne -b 0.0.0.0 -p 8001 woila_backend.asgi:application
```

## 🚀 **Méthode rapide (une seule commande) :**

```bash
cd /Users/macbookpro/Desktop/Developments/Personnals/Woila/woila_backend && source venv/bin/activate && export DJANGO_SETTINGS_MODULE=woila_backend.settings && daphne -b 0.0.0.0 -p 8001 woila_backend.asgi:application
```

## 📋 **Ou utiliser le script :**

```bash
cd /Users/macbookpro/Desktop/Developments/Personnals/Woila/woila_backend
./start_server.sh
```

## ✅ **Résultat attendu :**

```
INFO:     Starting server at http://0.0.0.0:8001
INFO:     Daphne ASGI server starting
INFO:     Application startup complete.
```

## 🌐 **URLs disponibles après démarrage :**

- **API REST:** `http://localhost:8001/api/v1/`
- **WebSocket Driver:** `ws://localhost:8001/ws/driver/28/`
- **WebSocket Customer:** `ws://localhost:8001/ws/customer/1/`

## 🧪 **Test rapide WebSocket :**

```bash
# Installer wscat si pas installé
npm install -g wscat

# Tester la connexion WebSocket
wscat -c "ws://localhost:8001/ws/driver/28/"
```

## 🔧 **Si ça ne marche toujours pas :**

### Vérifier l'installation de Daphne :
```bash
source venv/bin/activate
pip list | grep daphne
```

### Vérifier Django :
```bash
python manage.py check
```

### Vérifier les migrations :
```bash
python manage.py migrate
```

### Logs avec plus de détails :
```bash
daphne -b 0.0.0.0 -p 8001 -v 2 woila_backend.asgi:application
```

---
**Une fois le serveur démarré avec Daphne, les erreurs Redis et WebSocket 404 devraient disparaître ! 🎉**