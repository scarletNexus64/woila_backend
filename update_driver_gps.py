#!/usr/bin/env python3
"""
Script pour mettre à jour la position GPS d'un chauffeur
"""

import os
import sys
import django
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'woila_backend.settings')
django.setup()

from order.models import DriverStatus

def update_driver_gps(driver_id, latitude=None, longitude=None):
    """
    Mettre à jour la position GPS d'un chauffeur
    """
    try:
        # Position par défaut (Yaoundé, Cameroun)
        if latitude is None:
            latitude = Decimal('3.8480')
        if longitude is None:
            longitude = Decimal('11.5020')
        
        # Mettre à jour ou créer le status du chauffeur
        driver_status, created = DriverStatus.objects.get_or_create(
            driver_id=driver_id,
            defaults={
                'status': 'OFFLINE',
                'current_latitude': latitude,
                'current_longitude': longitude
            }
        )
        
        if not created:
            driver_status.current_latitude = latitude
            driver_status.current_longitude = longitude
            driver_status.save()
        
        print(f"✅ Chauffeur {driver_id} - Position GPS mise à jour: ({latitude}, {longitude})")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False

if __name__ == "__main__":
    # Mettre à jour la position du chauffeur 28
    print("🔧 Mise à jour position GPS chauffeur 28...")
    success = update_driver_gps(28)
    
    if success:
        print("🎉 Position GPS mise à jour avec succès!")
        print("📡 Maintenant la diffusion GPS devrait fonctionner")
    else:
        print("❌ Échec de la mise à jour")
        
    # Afficher le status actuel
    try:
        driver_status = DriverStatus.objects.get(driver_id=28)
        print(f"\n📊 Status actuel du chauffeur 28:")
        print(f"   - Status: {driver_status.status}")
        print(f"   - Latitude: {driver_status.current_latitude}")
        print(f"   - Longitude: {driver_status.current_longitude}")
        print(f"   - Dernière mise à jour: {driver_status.last_location_update}")
    except DriverStatus.DoesNotExist:
        print("⚠️ Chauffeur 28 non trouvé en base")