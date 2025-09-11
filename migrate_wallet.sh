#!/bin/bash

# Script pour migrer les nouvelles fonctionnalités de wallet

echo "🏦 Migration des APIs Wallet - Woila"
echo "=================================="

# Activar l'environnement virtuel si nécessaire
if [ -d "venv" ]; then
    echo "📁 Activation de l'environnement virtuel..."
    source venv/bin/activate
fi

# Créer les migrations
echo "📝 Création des migrations..."
python manage.py makemigrations api

# Appliquer les migrations
echo "🔄 Application des migrations..."
python manage.py migrate

# Vérifier que les ContentTypes existent
echo "🔍 Vérification des ContentTypes..."
python manage.py shell -c "
from django.contrib.contenttypes.models import ContentType
from api.models import UserDriver, UserCustomer

# Vérifier UserDriver ContentType
try:
    ct_driver = ContentType.objects.get(app_label='api', model='userdriver')
    print('✅ UserDriver ContentType existe:', ct_driver)
except ContentType.DoesNotExist:
    print('❌ UserDriver ContentType n\'existe pas')

# Vérifier UserCustomer ContentType  
try:
    ct_customer = ContentType.objects.get(app_label='api', model='usercustomer')
    print('✅ UserCustomer ContentType existe:', ct_customer)
except ContentType.DoesNotExist:
    print('❌ UserCustomer ContentType n\'existe pas')
    
print('')
print('🎉 Migration terminée!')
print('Vous pouvez maintenant tester les APIs Wallet.')
"

echo ""
echo "🚀 Pour tester les APIs:"
echo "1. Démarrez le serveur: python manage.py runserver"
echo "2. Accédez à: http://localhost:8000/api/docs/swagger/"
echo "3. Authentifiez-vous avec un token Bearer"
echo ""
echo "📋 Curl corrigé pour le test:"
echo "curl -X 'POST' \\"
echo "  'http://localhost:8000/api/v1/wallet/deposit/' \\"
echo "  -H 'accept: application/json' \\"
echo "  -H 'Authorization: Bearer b346b63c-ee55-44da-b966-cd2823eed006' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{"
echo "  \"amount\": 10000,"
echo "  \"phone_number\": \"+237658895572\","
echo "  \"description\": \"Rechargement wallet\""
echo "}'"