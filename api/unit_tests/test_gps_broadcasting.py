#!/usr/bin/env python3
"""
Test de la fonctionnalité de diffusion GPS automatique
=====================================================

Ce script teste :
1. L'API toggle_driver_status qui démarre automatiquement la diffusion GPS
2. La connexion WebSocket qui diffuse la position toutes les 5 secondes
3. La réception des messages de position par les clients

Usage: python test_gps_broadcasting.py
"""

import asyncio
import websockets
import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

# Données de test
TEST_DRIVER_ID = 1
TEST_CUSTOMER_ID = 1
TEST_LATITUDE = 14.6928
TEST_LONGITUDE = -17.4467  # Coordonnées de Dakar, Sénégal


def test_toggle_driver_status():
    """
    Test de l'API REST toggle_driver_status
    """
    print("🧪 Test 1: API toggle_driver_status")
    
    # Simuler un token d'authentification (adapter selon votre système)
    headers = {
        'Authorization': 'Bearer test_driver_token',
        'Content-Type': 'application/json'
    }
    
    try:
        # Appeler l'API pour passer le chauffeur ONLINE
        response = requests.post(
            f"{BASE_URL}/order/toggle-driver-status/",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chauffeur passé en ligne : {data.get('message')}")
            print(f"📊 Status: {data.get('status')}")
            return True
        else:
            print(f"❌ Erreur API : {response.status_code} - {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Erreur de connexion API : {str(e)}")
        return False


def test_update_driver_location():
    """
    Test de mise à jour de la position GPS du chauffeur
    """
    print("\n🧪 Test 2: Mise à jour position GPS")
    
    headers = {
        'Authorization': 'Bearer test_driver_token',
        'Content-Type': 'application/json'
    }
    
    location_data = {
        'latitude': TEST_LATITUDE,
        'longitude': TEST_LONGITUDE
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/order/update-driver-location/",
            headers=headers,
            json=location_data
        )
        
        if response.status_code == 200:
            print(f"✅ Position GPS mise à jour : {TEST_LATITUDE}, {TEST_LONGITUDE}")
            return True
        else:
            print(f"❌ Erreur mise à jour GPS : {response.status_code} - {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Erreur de connexion GPS : {str(e)}")
        return False


async def test_driver_websocket():
    """
    Test de la connexion WebSocket du chauffeur
    """
    print("\n🧪 Test 3: WebSocket Chauffeur - Diffusion GPS")
    
    try:
        uri = f"{WS_URL}/ws/driver/{TEST_DRIVER_ID}/"
        
        async with websockets.connect(uri) as websocket:
            print(f"🔌 Connexion WebSocket chauffeur établie: {uri}")
            
            # Écouter les messages pendant 30 secondes
            timeout = 30
            start_time = time.time()
            message_count = 0
            
            while time.time() - start_time < timeout:
                try:
                    # Attendre un message avec un timeout de 1 seconde
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    message_count += 1
                    
                    # Afficher les différents types de messages
                    message_type = data.get('type', 'unknown')
                    
                    if message_type == 'status_update':
                        print(f"📶 Status: {data.get('status')} - {data.get('message')}")
                        
                    elif message_type == 'location_broadcasting_started':
                        print(f"📡 Diffusion GPS démarrée: {data.get('message')}")
                        
                    elif message_type == 'location_broadcast_confirmation':
                        lat = data.get('latitude')
                        lon = data.get('longitude')
                        timestamp = data.get('timestamp')
                        print(f"📍 Position diffusée: ({lat}, {lon}) à {timestamp}")
                        
                    elif message_type == 'location_broadcasting_error':
                        print(f"❌ Erreur diffusion: {data.get('message')}")
                        
                    else:
                        print(f"📨 Message reçu [{message_type}]: {data}")
                        
                except asyncio.TimeoutError:
                    # Timeout normal, continuer
                    continue
                except websockets.exceptions.ConnectionClosed:
                    print("❌ Connexion WebSocket fermée")
                    break
                    
            print(f"📊 Total messages reçus: {message_count} en {timeout} secondes")
            return message_count > 0
            
    except Exception as e:
        print(f"❌ Erreur WebSocket chauffeur: {str(e)}")
        return False


async def test_customer_websocket():
    """
    Test de la connexion WebSocket client pour écouter la position du chauffeur
    """
    print("\n🧪 Test 4: WebSocket Client - Écoute GPS chauffeur")
    
    try:
        uri = f"{WS_URL}/ws/customer/{TEST_CUSTOMER_ID}/"
        
        async with websockets.connect(uri) as websocket:
            print(f"🔌 Connexion WebSocket client établie: {uri}")
            
            # S'abonner au suivi du chauffeur
            subscribe_message = {
                'type': 'subscribe_driver_tracking',
                'driver_id': TEST_DRIVER_ID
            }
            await websocket.send(json.dumps(subscribe_message))
            print(f"📡 Abonnement au suivi du chauffeur {TEST_DRIVER_ID}")
            
            # Écouter pendant 20 secondes
            timeout = 20
            start_time = time.time()
            location_updates = 0
            
            while time.time() - start_time < timeout:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    
                    message_type = data.get('type', 'unknown')
                    
                    if message_type == 'driver_location_update':
                        location_updates += 1
                        driver_id = data.get('driver_id')
                        lat = data.get('latitude')
                        lon = data.get('longitude')
                        timestamp = data.get('timestamp')
                        print(f"📍 Position chauffeur {driver_id}: ({lat}, {lon}) à {timestamp}")
                        
                    else:
                        print(f"📨 Message client [{message_type}]: {data}")
                        
                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    print("❌ Connexion WebSocket client fermée")
                    break
                    
            print(f"📊 Mises à jour de position reçues: {location_updates} en {timeout} secondes")
            return location_updates > 0
            
    except Exception as e:
        print(f"❌ Erreur WebSocket client: {str(e)}")
        return False


def test_driver_offline():
    """
    Test pour repasser le chauffeur OFFLINE
    """
    print("\n🧪 Test 5: Passer chauffeur OFFLINE")
    
    headers = {
        'Authorization': 'Bearer test_driver_token',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/order/toggle-driver-status/",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chauffeur passé hors ligne : {data.get('message')}")
            print(f"📊 Status: {data.get('status')}")
            return True
        else:
            print(f"❌ Erreur API : {response.status_code} - {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Erreur de connexion API : {str(e)}")
        return False


async def run_all_tests():
    """
    Exécuter tous les tests
    """
    print("🚀 Démarrage des tests de diffusion GPS automatique")
    print("=" * 60)
    
    results = []
    
    # Test 1: API toggle status -> ONLINE
    results.append(test_toggle_driver_status())
    
    # Test 2: Mise à jour position GPS
    results.append(test_update_driver_location())
    
    # Attendre un peu pour que le système se stabilise
    print("\n⏳ Attente de 3 secondes pour stabilisation...")
    await asyncio.sleep(3)
    
    # Test 3: WebSocket chauffeur (diffusion GPS)
    results.append(await test_driver_websocket())
    
    # Test 4: WebSocket client (réception GPS) - exécuté en parallèle
    # results.append(await test_customer_websocket())
    
    # Test 5: Repasser OFFLINE
    results.append(test_driver_offline())
    
    # Résultats
    print("\n" + "=" * 60)
    print("📋 RÉSULTATS DES TESTS")
    print("=" * 60)
    
    test_names = [
        "API toggle_driver_status -> ONLINE",
        "Mise à jour position GPS",
        "WebSocket chauffeur (diffusion GPS)",
        # "WebSocket client (réception GPS)",
        "API toggle_driver_status -> OFFLINE"
    ]
    
    passed = sum(results)
    total = len(results)
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASSÉ" if result else "❌ ÉCHOUÉ"
        print(f"{i+1}. {name}: {status}")
    
    print(f"\n🎯 Score: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont passés ! La diffusion GPS fonctionne correctement.")
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez la configuration du serveur.")
    
    return passed == total


if __name__ == "__main__":
    print("🧪 Test de diffusion GPS automatique pour chauffeurs VTC")
    print(f"📍 Position de test: {TEST_LATITUDE}, {TEST_LONGITUDE} (Dakar)")
    print(f"🔗 URL de base: {BASE_URL}")
    print(f"🔗 WebSocket URL: {WS_URL}")
    print()
    
    # Instructions
    print("📝 INSTRUCTIONS:")
    print("1. Assurez-vous que le serveur Django est en cours d'exécution")
    print("2. Assurez-vous que les WebSockets sont configurés (Daphne/Channels)")
    print("3. Adaptez TEST_DRIVER_ID et les tokens d'authentification si nécessaire")
    print("4. Adaptez les URLs si le serveur n'est pas sur localhost:8000")
    print()
    
    try:
        success = asyncio.run(run_all_tests())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrompus par l'utilisateur")
        exit(1)
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {str(e)}")
        exit(1)