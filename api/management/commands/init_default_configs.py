#!/usr/bin/env python3
"""
Commande Django pour initialiser les configurations par défaut de Woilà
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from api.models import GeneralConfig


class Command(BaseCommand):
    help = '🔧 Initialise les configurations par défaut de Woilà'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la réinitialisation même si des configurations existent déjà',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affichage détaillé',
        )

    def handle(self, *args, **options):
        """Exécute la commande d'initialisation"""
        
        force = options.get('force', False)
        verbose = options.get('verbose', False)
        
        # Vérifier si des configurations existent déjà
        existing_configs = GeneralConfig.objects.count()
        
        if existing_configs > 0 and not force:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  {existing_configs} configuration(s) déjà présente(s). "
                    f"Utilisez --force pour réinitialiser."
                )
            )
            return
        
        if force and existing_configs > 0:
            if verbose:
                self.stdout.write(
                    self.style.WARNING(
                        f"🗑️  Suppression de {existing_configs} configuration(s) existante(s)..."
                    )
                )
            GeneralConfig.objects.all().delete()
        
        # Charger les fixtures
        self.stdout.write("🔧 Chargement des configurations par défaut...")
        
        try:
            call_command('loaddata', 'default_configs', verbosity=0)
            
            # Vérifier le résultat
            new_count = GeneralConfig.objects.count()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ {new_count} configuration(s) chargée(s) avec succès!"
                )
            )
            
            if verbose:
                self.stdout.write("\n📋 Configurations chargées:")
                for config in GeneralConfig.objects.all().order_by('search_key'):
                    status = "✅" if config.active else "❌"
                    self.stdout.write(
                        f"  {status} {config.nom} = {config.valeur}"
                    )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f"❌ Erreur lors du chargement des configurations: {e}"
                )
            )