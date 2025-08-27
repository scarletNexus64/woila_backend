#!/usr/bin/env python3
"""
Script pour forcer une position GPS au chauffeur 29 (test)
"""
import os
import sys
import django
from django.conf import settings

# Setup Django environment
sys.path.append('/Users/macbookpro/Desktop/Developments/Personnals/Woila/woila_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'woila_backend.settings')
django.setup()

from order.models import DriverStatus
from django.utils import timezone

def fix_driver_29_gps():
    """Force une position GPS de test pour le chauffeur 29"""
    
    try:
        driver_status = DriverStatus.objects.get(driver_id=29)
        
        # Position près du chauffeur 28 pour les tests
        test_latitude = 3.8970  # Proche de Yaoundé
        test_longitude = 11.5472
        
        driver_status.current_latitude = test_latitude
        driver_status.current_longitude = test_longitude
        driver_status.last_location_update = timezone.now()
        driver_status.save()
        
        print(f"✅ Position GPS mise à jour pour chauffeur 29:")
        print(f"   Latitude: {test_latitude}")
        print(f"   Longitude: {test_longitude}")
        print(f"   Timestamp: {driver_status.last_location_update}")
        
        return True
        
    except DriverStatus.DoesNotExist:
        print("❌ DriverStatus non trouvé pour chauffeur 29")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Correction GPS chauffeur 29...")
    success = fix_driver_29_gps()
    if success:
        print("🎉 Test terminé - Le chauffeur VIP devrait maintenant apparaître!")
    else:
        print("💔 Échec de la correction GPS")