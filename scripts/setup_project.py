#!/usr/bin/env python3
"""
Script d'installation et configuration automatique du projet Woilà Backend
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

def setup_project():
    """Configure automatiquement le projet après clonage"""
    
    print("🚗 Configuration automatique de Woilà Backend...")
    print("=" * 50)
    
    # Assurer qu'on est dans le bon répertoire (racine du projet)
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(current_dir)
    
    # Ajouter le répertoire du projet au Python path
    sys.path.insert(0, current_dir)
    
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'woila_backend.settings')
    django.setup()
    
    print("1️⃣  Application des migrations...")
    try:
        execute_from_command_line(['manage.py', 'migrate'])
        print("   ✅ Migrations appliquées avec succès")
    except Exception as e:
        print(f"   ❌ Erreur lors des migrations: {e}")
        return False
    
    print("\n2️⃣  Chargement des configurations par défaut...")
    try:
        execute_from_command_line(['manage.py', 'init_default_configs', '--verbose'])
        print("   ✅ Configurations par défaut chargées")
    except Exception as e:
        print(f"   ❌ Erreur lors du chargement des configurations: {e}")
        # Ce n'est pas critique, on continue
    
    print("\n3️⃣  Création d'un superutilisateur (optionnel)...")
    try:
        from django.contrib.auth.models import User
        if not User.objects.filter(is_superuser=True).exists():
            print("   Aucun superutilisateur trouvé.")
            print("   Pour créer un superutilisateur, exécutez: python3 manage.py createsuperuser")
        else:
            print("   ✅ Superutilisateur déjà présent")
    except Exception as e:
        print(f"   ⚠️  Impossible de vérifier les superutilisateurs: {e}")
    
    print("\n🎉 Configuration terminée!")
    print("\n📋 Prochaines étapes:")
    print("   • Démarrer le serveur: python3 manage.py runserver")
    print("   • Accéder à l'admin: http://127.0.0.1:8000/admin/")
    print("   • Consulter l'API: http://127.0.0.1:8000/api/swagger/")
    print("   • Configurations: http://127.0.0.1:8000/admin/api/generalconfig/")
    
    return True


if __name__ == '__main__':
    success = setup_project()
    sys.exit(0 if success else 1)