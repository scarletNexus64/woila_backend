#!/usr/bin/env python
"""
Test script pour vérifier la validation véhicule
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'woila_backend.settings')
django.setup()

from api.models import UserDriver, Vehicle
from order.models import DriverStatus

def test_vehicle_validation():
    print('=== CHAUFFEURS EXISTANTS ===')
    for driver in UserDriver.objects.all()[:3]:
        vehicles = Vehicle.objects.filter(driver=driver)
        active_online = vehicles.filter(is_active=True, is_online=True).count()
        print(f'Chauffeur {driver.id}: {driver.name} - {vehicles.count()} véhicules - {active_online} actifs+en service')

    print('\n=== TEST VALIDATION ===')
    test_driver = UserDriver.objects.first()
    if test_driver:
        print(f'Test avec chauffeur: {test_driver.name} (ID: {test_driver.id})')
        
        vehicles = Vehicle.objects.filter(driver=test_driver)
        active_online = vehicles.filter(is_active=True, is_online=True).count()
        
        print(f'Véhicules: {vehicles.count()} total, {active_online} actifs+en service')
        
        if active_online == 0:
            print('✅ PARFAIT - Ce chauffeur n a pas de véhicule actif+en service')
            print('Il devrait recevoir une erreur lors du passage en ligne')
        else:
            print(f'⚠️ Ce chauffeur a {active_online} véhicule(s) actif(s)+en service')
            print('Il devrait pouvoir passer en ligne')

if __name__ == '__main__':
    test_vehicle_validation()