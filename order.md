je suis entrain de travailler sur le process de la commande de mon projet de VTC, tu vera les fichiers concernant l'api en django rest framework dans la partie section project ici meme. inspecte ceque jai fais ici et tu me dis dabord ceque tu as compris de cequi est là. et voici cequ'on doit faire, voici le process, je t decris le process dabord : 
* le driver passe en ON pour etre eligible a recevoir la commande
* le client lance la recherche dans son application et on trouve pour lui le chauffeur le plus proche de lui ( on va gerer avec la distance noublie pas ce detail, je sais pas si on va comparer les longitude et latitude, bref tu vas proposer )
* lorsqu'on trouve des chauffeurs disponible donc il vera lui  dans son interface: Taxi Jaune (sil ya deux chauffeurs taxi jaunes, Confort ( sil ya 4 chauffeurs .. ), et. sil. ya aucun chauffeur dans le type de taxi on affiche pas. en affichant donc le type de vehicule qu'il veut, les prix sont deja calculé meme ( dans les fichiers dans la section du projet tu vera que les prix cest en fonction de la distance ou il veut aller (car le client va rentrer sa source et sa destination avant de choisir un type de vehicule), en fonction du type de vehicule, ... et d'autre config que tu vera, je te laisse inspecter les fichier pour comprendre ainsi que le fichier admin.py ou je fais les config (en fonction des pays, des zones ciblé ou ce sont les prix fixe ... ). là le client vera que le prix va varier entre tel et tel ... ou un prix sensiblement egale. 
* il choisi le type de vehicule et on lance l'appel au groupe de chauffeurs concerné (on check sur le. premier dans le pool sil ne decroche pas ou naccepte pas on passe. au suivant ainsi de suite, le temps d'attente du chauffeur est aussi configuré ( MAX_WAITING_TIME )
* il choisi le type de paiement ( pour l'instant j'ai pas encore de table pour. definir les types de paiements qu'on aura labas. mais. il doit choisir sil doit avoir OM, MOMO, CASH, WALLET ( jai au. moins son wallet), on va ajouter ca, paymentType ou on va mettre
* le chauffeur. accepte la commande et le cclient sait qu'il ya un chauffeur qui. arrive ( il va le voir se deplacer sur la map ) et là letat de la commande est EN ATTENTE, ce nest plus en brouillon
* une fois sur place le. chauffeur click sur demarrer la course alors et là cest en PENDING
* une fois arrivé il click sur TERMINE et on le chauffeur et lien les deux ont le prix de la course ( le prix peut etre legerement update a cause du trajet changé ).  LA COMMANDE EST ALORS A LETAT DONE et Non CANCEL
* le client peut alors payer ( ici laisson )

Okay il est question que tu comprenne dabord cequi est là, tu fais l'inventaire des api endpoint qu'on aura, et les nouvelles models qu'on aura les nouvelles librairie qu'on doit installer check mon requirements.txt qui es là pour comprendre dabord cequi es là dabord ne scan pas les fichiers de la machine reste ici, jai laissé tout le necessaire dans la section project knowledge.

et ensuite tu dresse un plan alors, et on doit tester tout ca de facon unitaire et tu ve me montrer comment tester ca dans postman aussi ou un outils. de websocket client serveur et tout. nexagere pas, ne fais pas ceque jai pas dis stp nexagere pas. soit intelligent on est dans le vtc, sijai oublié un dettail rappel moi



📊 INVENTAIRE DE L'EXISTANT
✅ Ce qui est déjà en place :
Models existants :
UserDriver, UserCustomer (dans api)
Vehicle, VehicleType, VehicleBrand, VehicleModel, VehicleColor
City, VipZone, Country
GeneralConfig (configurations système)
Wallet, Token (authentification)
Order (modèle de commande avec tous les champs nécessaires)
DriverStatus (statut en ligne/hors ligne du chauffeur)
OrderTracking (suivi des événements de commande)
Services :
PricingService : Calcul des prix (base, distance, type véhicule, ville, zone VIP)
OrderService : Gestion des commandes (recherche chauffeurs, calcul distance)
WebSocket (Channels) :
Configuration Redis en place
DriverConsumer et CustomerConsumer déjà créés
Routing websocket configuré
Configurations (GeneralConfig) :
STD_PRICELIST_ORDER : Prix de base
PRICE_PER_KM : Prix par kilomètre
MAX_WAITING_TIME : Temps d'attente max
❌ Ce qui manque :
📋 PLAN D'IMPLÉMENTATION
1. Nouveaux Models à ajouter :
python
# Dans order/models.py

class PaymentMethod(models.Model):
    """Types de paiement disponibles"""
    PAYMENT_TYPES = [
        ('CASH', 'Espèces'),
        ('OM', 'Orange Money'),
        ('MOMO', 'MTN Mobile Money'),
        ('WALLET', 'Portefeuille'),
    ]
    
    type = models.CharField(max_length=20, choices=PAYMENT_TYPES, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    icon = models.CharField(max_length=255, blank=True)
    
# Ajouter à Order :
payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True)
payment_status = models.CharField(max_length=20, choices=[
    ('PENDING', 'En attente'),
    ('PAID', 'Payé'),
    ('FAILED', 'Échoué')
], default='PENDING')
2. API Endpoints nécessaires :
Endpoint	Méthode	Description
/api/v1/order/driver/toggle-status/	POST	Passer en ligne/hors ligne
/api/v1/order/driver/update-location/	POST	MAJ position GPS
/api/v1/order/customer/search-drivers/	POST	Rechercher chauffeurs disponibles
/api/v1/order/customer/calculate-price/	POST	Calculer prix estimé
/api/v1/order/customer/create/	POST	Créer commande
/api/v1/order/driver/accept/{order_id}/	POST	Accepter commande
/api/v1/order/driver/start/{order_id}/	POST	Démarrer course
/api/v1/order/driver/complete/{order_id}/	POST	Terminer course
/api/v1/order/cancel/{order_id}/	POST	Annuler commande
/api/v1/order/payment-methods/	GET	Liste méthodes paiement
/api/v1/order/{order_id}/	GET	Détails commande
3. Nouvelles librairies à installer :
bash
# Déjà dans requirements.txt :
# ✅ channels, channels-redis (WebSocket)
# ✅ redis (cache et WebSocket)
# ✅ djangorestframework
# ✅ Pillow (images)

# À ajouter si nécessaire :
pip install geopy  # Pour calculs de distance plus précis
pip install celery  # Pour tâches asynchrones (notifications push)
4. Flux WebSocket amélioré :
python
# Messages WebSocket

# Client → Serveur :
{
    "type": "search_drivers",
    "pickup_lat": 4.0511,
    "pickup_lng": 9.7679,
    "destination_lat": 4.0300,
    "destination_lng": 9.7100
}

# Serveur → Client :
{
    "type": "drivers_available",
    "vehicle_types": [
        {
            "type": "taxi_jaune",
            "count": 2,
            "estimated_price": {"min": 2500, "max": 3000},
            "nearest_driver_distance": 0.5
        }
    ]
}

# Notification temps réel driver :
{
    "type": "new_order_request",
    "order_id": "uuid",
    "pickup_address": "...",
    "destination_address": "...",
    "estimated_price": 3000,
    "timeout": 30  # secondes
}
5. Tests avec Postman/WebSocket :
Collection Postman :
Authentification Driver
json
POST /api/v1/login/driver/
{
    "phone_number": "237600000001",
    "password": "test123"
}
Driver passe en ligne
json
POST /api/v1/order/driver/toggle-status/
Headers: Authorization: Bearer {token}
{
    "status": "ONLINE",
    "latitude": 4.0511,
    "longitude": 9.7679
}
Client recherche chauffeurs
json
POST /api/v1/order/customer/search-drivers/
Headers: Authorization: Bearer {token}
{
    "pickup_lat": 4.0511,
    "pickup_lng": 9.7679,
    "destination_lat": 4.0300,
    "destination_lng": 9.7100,
    "vehicle_type_id": 1
}
Test WebSocket (wscat ou Postman) :
bash
# Installer wscat
npm install -g wscat

# Connexion driver
wscat -c ws://localhost:8000/ws/driver/{driver_id}/

# Connexion client  
wscat -c ws://localhost:8000/ws/customer/{customer_id}/
6. Script de test complet :
python
# tests/test_order_flow.py

import asyncio
import websockets
import json

async def test_order_flow():
    # 1. Driver se connecte
    driver_ws = await websockets.connect('ws://localhost:8000/ws/driver/1/')
    
    # 2. Client se connecte
    customer_ws = await websockets.connect('ws://localhost:8000/ws/customer/1/')
    
    # 3. Client cherche drivers
    await customer_ws.send(json.dumps({
        'type': 'search_drivers',
        'pickup_lat': 4.0511,
        'pickup_lng': 9.7679,
        'destination_lat': 4.0300,
        'destination_lng': 9.7100
    }))
    
    # 4. Driver reçoit notification
    order_request = await driver_ws.recv()
    print(f"Driver received: {order_request}")
    
    # 5. Driver accepte
    await driver_ws.send(json.dumps({
        'type': 'accept_order',
        'order_id': '...'
    }))
    
    # Continue...
7. Détails importants oubliés :
Gestion du pool de chauffeurs : Ordre de priorité (plus proche d'abord)
Timeout automatique : Si chauffeur ne répond pas dans MAX_WAITING_TIME
Mise à jour prix final : Recalculer selon distance réelle
Historique positions : Tracker le trajet pour sécurité
Ratings : Système de notation driver/client
8. Prochaines étapes :
Migration base de données pour nouveaux champs
Implémenter les ViewSets pour les endpoints
Améliorer les consumers WebSocket
Créer les serializers pour validation
Tests unitaires pour chaque composant
Voulez-vous que je commence par implémenter une partie spécifique ? Je peux créer :

Les nouveaux models avec migrations
Les API endpoints complets
Le système WebSocket amélioré
Les tests Postman/WebSocket
Dites-moi par où vous voulez commencer ! 🚀




super il faut une table pour rating aussi on doit ajoute la table, merci on va prendre en compte tout ca

Gestion du pool de chauffeurs : Ordre de priorité (plus proche d'abord)
Timeout automatique : Si chauffeur ne répond pas dans MAX_WAITING_TIME
Mise à jour prix final : Recalculer selon distance réelle
Historique positions : Tracker le trajet pour sécurité
Ratings : Système de notation driver/client
okay fais une check liste alors et on commence, propre par ordre de priorité

Edit
🚀 CHECKLIST COMPLÈTE - IMPLÉMENTATION SYSTÈME DE COMMANDE VTC
PHASE 1 : FONDATIONS (Priorité HAUTE) 🔴
📊 1.1 - Modèles de données
 Créer model PaymentMethod (CASH, OM, MOMO, WALLET)
 Créer model Rating (note driver/client + commentaires)
 Créer model TripTracking (historique positions GPS pendant course)
 Ajouter champs manquants à Order:
 payment_method (ForeignKey)
 payment_status (PENDING, PAID, FAILED)
 driver_rating (1-5 étoiles)
 customer_rating (1-5 étoiles)
 final_price (prix ajusté après course)
 waiting_time (temps d'attente client)
 Créer model DriverPool (gestion ordre d'appel des chauffeurs)
 Faire les migrations
🔧 1.2 - Services de base
 Améliorer OrderService.find_nearby_drivers() avec tri par distance
 Implémenter calculate_real_distance() avec geopy
 Créer DriverPoolService pour gestion séquentielle des appels
 Créer PaymentService pour gestion paiements
 Ajouter méthode update_final_price() dans PricingService
PHASE 2 : APIs REST (Priorité HAUTE) 🔴
🌐 2.1 - Endpoints Driver
 POST /api/v1/order/driver/toggle-status/ - Passer ON/OFF
 POST /api/v1/order/driver/update-location/ - MAJ position GPS
 POST /api/v1/order/driver/accept/{order_id}/ - Accepter commande
 POST /api/v1/order/driver/reject/{order_id}/ - Refuser commande
 POST /api/v1/order/driver/arrived/{order_id}/ - Arrivé sur place
 POST /api/v1/order/driver/start/{order_id}/ - Démarrer course
 POST /api/v1/order/driver/complete/{order_id}/ - Terminer course
 GET /api/v1/order/driver/current/ - Commande en cours
 GET /api/v1/order/driver/history/ - Historique courses
🌐 2.2 - Endpoints Client
 POST /api/v1/order/customer/search-drivers/ - Chercher chauffeurs
 POST /api/v1/order/customer/estimate-price/ - Estimer prix
 POST /api/v1/order/customer/create/ - Créer commande
 POST /api/v1/order/customer/cancel/{order_id}/ - Annuler
 GET /api/v1/order/customer/track/{order_id}/ - Suivre commande
 POST /api/v1/order/customer/rate/{order_id}/ - Noter course
 GET /api/v1/order/customer/history/ - Historique
🌐 2.3 - Endpoints communs
 GET /api/v1/order/payment-methods/ - Méthodes de paiement
 GET /api/v1/order/{order_id}/ - Détails commande
 GET /api/v1/order/vehicle-types/available/ - Types véhicules disponibles
PHASE 3 : WEBSOCKET TEMPS RÉEL (Priorité HAUTE) 🔴
🔌 3.1 - Consumer Driver
 Gérer connexion/déconnexion avec MAJ statut
 Handler location_update - MAJ position temps réel
 Handler accept_order - Accepter commande
 Handler reject_order - Refuser commande
 Handler start_trip - Démarrer course
 Handler complete_trip - Terminer course
 Broadcast position aux clients pendant course
🔌 3.2 - Consumer Client
 Handler search_drivers - Recherche temps réel
 Handler create_order - Création commande
 Handler cancel_order - Annulation
 Recevoir MAJ position driver en temps réel
 Recevoir notifications changement statut commande
🔌 3.3 - Système de pool/timeout
 Implémenter queue d'appel séquentiel des drivers
 Timer automatique MAX_WAITING_TIME (30 sec par défaut)
 Passer au driver suivant si timeout
 Notifier client si aucun driver disponible
PHASE 4 : LOGIQUE MÉTIER (Priorité MOYENNE) 🟡
💼 4.1 - Gestion du pool de chauffeurs
 Algorithme de tri par distance (Haversine)
 Filtrer par type de véhicule disponible
 Gérer les chauffeurs BUSY/ONLINE
 Système de réservation temporaire pendant attente réponse
💼 4.2 - Calcul de prix
 Prix estimé (avant course) avec fourchette min/max
 Prix final basé sur distance réelle
 Gestion suppléments (attente, bagages, etc.)
 Historique des modifications de prix
💼 4.3 - Tracking GPS
 Enregistrer position toutes les 10 secondes pendant course
 Calculer distance parcourue réelle
 Détecter les déviations anormales
 Archive du trajet complet
PHASE 5 : TESTS & VALIDATION (Priorité MOYENNE) 🟡
🧪 5.1 - Tests unitaires
 Tests models (Order, Rating, PaymentMethod)
 Tests services (Pricing, Order, Payment)
 Tests serializers (validation données)
 Tests consumers WebSocket
🧪 5.2 - Tests d'intégration
 Scénario complet : recherche → commande → course → paiement
 Test timeout et passage driver suivant
 Test annulation à différentes étapes
 Test calcul prix (estimé vs final)
🧪 5.3 - Collection Postman
 Créer environnement avec variables
 Endpoints authentification
 Flow driver complet
 Flow client complet
 Tests WebSocket avec wscat
PHASE 6 : SYSTÈME DE NOTATION (Priorité BASSE) 🟢
⭐ 6.1 - Rating bidirectionnel
 API notation driver → client
 API notation client → driver
 Calcul moyenne des notes
 Blocage si note < 3.0
 Système de commentaires
⭐ 6.2 - Statistiques
 Dashboard driver (courses, revenus, notes)
 Dashboard client (historique, dépenses)
 Rapports administrateur
PHASE 7 : OPTIMISATIONS (Priorité BASSE) 🟢
⚡ 7.1 - Performance
 Cache Redis pour positions drivers
 Index database sur coordonnées GPS
 Pagination historiques
 Compression messages WebSocket
⚡ 7.2 - Sécurité
 Rate limiting APIs
 Validation coordonnées GPS
 Chiffrement données sensibles
 Logs d'audit
📝 ORDRE D'EXÉCUTION RECOMMANDÉ
Semaine 1 🏃‍♂️
✅ Phase 1.1 - Modèles de données
✅ Phase 1.2 - Services de base
✅ Phase 2.1 - APIs Driver essentielles
Semaine 2 🏃‍♂️
✅ Phase 2.2 - APIs Client
✅ Phase 3.1 & 3.2 - WebSocket de base
✅ Phase 3.3 - Système pool/timeout
Semaine 3 🏃‍♂️
✅ Phase 4 - Logique métier complète
✅ Phase 5 - Tests
Semaine 4 🏃‍♂️
✅ Phase 6 - Système notation
✅ Phase 7 - Optimisations
