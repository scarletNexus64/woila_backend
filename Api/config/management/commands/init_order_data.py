from django.core.management.base import BaseCommand
from django.db import transaction

from order.models import PaymentMethod
from core.models import GeneralConfig


class Command(BaseCommand):
    help = 'Initialise les données de base pour le système de commande VTC'

    def handle(self, *args, **kwargs):
        self.stdout.write('🚀 Initialisation des données de base...\n')
        
        # Créer les méthodes de paiement
        self.create_payment_methods()
        
        # Créer les configurations générales
        self.create_general_configs()
        
        self.stdout.write(self.style.SUCCESS('\n✅ Initialisation terminée avec succès!'))
    
    @transaction.atomic
    def create_payment_methods(self):
        """Crée les méthodes de paiement par défaut"""
        self.stdout.write('💳 Création des méthodes de paiement...')
        
        payment_methods = [
            {
                'type': 'CASH',
                'name': 'Espèces',
                'description': 'Paiement en espèces directement au chauffeur',
                'icon': '💵',
                'is_active': True,
                'min_amount': 500,
                'max_amount': None
            },
            {
                'type': 'OM',
                'name': 'Orange Money',
                'description': 'Paiement via Orange Money',
                'icon': '📱',
                'is_active': True,
                'min_amount': 100,
                'max_amount': 1000000
            },
            {
                'type': 'MOMO',
                'name': 'MTN Mobile Money',
                'description': 'Paiement via MTN Mobile Money',
                'icon': '📲',
                'is_active': True,
                'min_amount': 100,
                'max_amount': 1000000
            },
            {
                'type': 'WALLET',
                'name': 'Portefeuille Woila',
                'description': 'Paiement via le portefeuille intégré Woila',
                'icon': '👛',
                'is_active': True,
                'min_amount': 100,
                'max_amount': 500000
            }
        ]
        
        for pm_data in payment_methods:
            payment_method, created = PaymentMethod.objects.get_or_create(
                type=pm_data['type'],
                defaults=pm_data
            )
            if created:
                self.stdout.write(f"  ✅ Créé: {payment_method.name}")
            else:
                self.stdout.write(f"  ⏭️  Existe déjà: {payment_method.name}")
    
    @transaction.atomic
    def create_general_configs(self):
        """Crée les configurations générales pour le système de commande"""
        self.stdout.write('\n⚙️  Création des configurations générales...')
        
        configs = [
            {
                'nom': 'Temps d\'attente maximum chauffeur',
                'search_key': 'MAX_DRIVER_WAITING_TIME',
                'valeur': '30',
                'active': True
            },
            {
                'nom': 'Prix par minute d\'attente',
                'search_key': 'PRICE_PER_WAITING_MINUTE',
                'valeur': '50',
                'active': True
            },
            {
                'nom': 'Rayon de recherche chauffeurs (km)',
                'search_key': 'DRIVER_SEARCH_RADIUS',
                'valeur': '5',
                'active': True
            },
            {
                'nom': 'Intervalle de tracking GPS (secondes)',
                'search_key': 'GPS_TRACKING_INTERVAL',
                'valeur': '10',
                'active': True
            },
            {
                'nom': 'Commission plateforme (%)',
                'search_key': 'PLATFORM_COMMISSION',
                'valeur': '20',
                'active': True
            },
            {
                'nom': 'Note minimum chauffeur',
                'search_key': 'MIN_DRIVER_RATING',
                'valeur': '3.0',
                'active': True
            },
            {
                'nom': 'Note minimum client',
                'search_key': 'MIN_CUSTOMER_RATING',
                'valeur': '3.0',
                'active': True
            },
            {
                'nom': 'Heure début tarif nuit',
                'search_key': 'NIGHT_FARE_START_HOUR',
                'valeur': '22',
                'active': True
            },
            {
                'nom': 'Heure fin tarif nuit',
                'search_key': 'NIGHT_FARE_END_HOUR',
                'valeur': '6',
                'active': True
            },
            {
                'nom': 'Nombre max de rejets consécutifs',
                'search_key': 'MAX_CONSECUTIVE_REJECTIONS',
                'valeur': '3',
                'active': True
            },
            {
                'nom': 'Temps de pause après rejets (minutes)',
                'search_key': 'REJECTION_PAUSE_TIME',
                'valeur': '15',
                'active': True
            },
            {
                'nom': 'Distance max pour course (km)',
                'search_key': 'MAX_TRIP_DISTANCE',
                'valeur': '100',
                'active': True
            },
            {
                'nom': 'Délai max annulation gratuite (minutes)',
                'search_key': 'FREE_CANCELLATION_TIME',
                'valeur': '5',
                'active': True
            },
            {
                'nom': 'Frais d\'annulation',
                'search_key': 'CANCELLATION_FEE',
                'valeur': '500',
                'active': True
            }
        ]
        
        for config_data in configs:
            config, created = GeneralConfig.objects.get_or_create(
                search_key=config_data['search_key'],
                defaults=config_data
            )
            if created:
                self.stdout.write(f"  ✅ Créé: {config.nom} = {config.valeur}")
            else:
                self.stdout.write(f"  ⏭️  Existe déjà: {config.nom} = {config.valeur}")
