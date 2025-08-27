#!/bin/bash

# Script de démarrage du serveur Woila avec support WebSocket
# ==========================================================

echo "🚀 Démarrage du serveur Woila Backend avec WebSocket support"
echo "================================================================="

# Activer l'environnement virtuel
if [ -d "venv" ]; then
    echo "🐍 Activation de l'environnement virtuel..."
    source venv/bin/activate
    echo "✅ Environnement virtuel activé"
else
    echo "❌ Environnement virtuel 'venv' non trouvé"
    echo "   Créez-le avec: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Configurer Django
echo "⚙️ Configuration de Django..."
export DJANGO_SETTINGS_MODULE=woila_backend.settings
export PYTHONPATH=$PWD:$PYTHONPATH

# Vérifier les dépendances
echo "🔍 Vérification des dépendances..."

if ! python -c "import daphne" 2>/dev/null; then
    echo "❌ Daphne non installé. Installation en cours..."
    pip install daphne
fi

if ! python -c "import channels" 2>/dev/null; then
    echo "❌ Channels non installé. Installation en cours..."
    pip install channels
fi

# Appliquer les migrations si nécessaire
echo "🗃️ Vérification des migrations..."
python manage.py migrate --check > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "📝 Application des migrations..."
    python manage.py migrate
fi

# Configuration serveur
HOST="0.0.0.0"
PORT="8001"

echo ""
echo "📡 Configuration serveur:"
echo "   - Host: $HOST"
echo "   - Port: $PORT"
echo "   - WebSocket: ✅ Activé"
echo "   - Channels Layer: InMemoryChannelLayer (développement)"
echo ""

# URLs importantes
echo "🔗 URLs importantes:"
echo "   - API REST: http://$HOST:$PORT/api/v1/"
echo "   - Admin: http://$HOST:$PORT/admin/"
echo "   - WebSocket Driver: ws://$HOST:$PORT/ws/driver/{driver_id}/"
echo "   - WebSocket Customer: ws://$HOST:$PORT/ws/customer/{customer_id}/"
echo ""

# Configurer Django
echo "⚙️ Configuration de Django..."
export DJANGO_SETTINGS_MODULE=woila_backend.settings
export PYTHONPATH=$PWD:$PYTHONPATH

# Démarrer le serveur avec Daphne
echo "🚀 Démarrage du serveur avec Daphne..."
echo "   Ctrl+C pour arrêter"
echo ""

# Option 1: Daphne simple (recommandé pour développement)
exec daphne -b $HOST -p $PORT woila_backend.asgi:application

# Option 2: Daphne avec logs détaillés (décommentez si besoin)
# exec daphne -b $HOST -p $PORT -v 2 woila_backend.asgi:application