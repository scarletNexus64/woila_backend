# Migrations pour charger automatiquement les configurations par défaut

from django.db import migrations
from django.core.management import call_command


def load_default_configs(apps, schema_editor):
    """
    Charge les configurations par défaut depuis les fixtures
    """
    # Utiliser le modèle via apps.get_model pour éviter les problèmes de migration
    GeneralConfig = apps.get_model('api', 'GeneralConfig')
    
    # Ne charger les fixtures que si aucune configuration n'existe
    if not GeneralConfig.objects.exists():
        # Définir les configurations directement dans la migration
        default_configs = [
            {
                "nom": "⏰ Temps d'attente maximum (minutes)",
                "search_key": "MAX_WAITING_TIME",
                "valeur": "30",
                "active": True
            },
            {
                "nom": "🎁 Bonus de bienvenue",
                "search_key": "WELCOME_BONUS_AMOUNT", 
                "valeur": "5000",
                "active": True
            },
            {
                "nom": "💳 Montant minimum de recharge",
                "search_key": "MIN_RECHARGE_AMOUNT",
                "valeur": "1000",
                "active": True
            },
            {
                "nom": "💸 Commission de la plateforme (%)",
                "search_key": "PLATFORM_COMMISSION_RATE",
                "valeur": "15",
                "active": True
            },
            {
                "nom": "📧 Email de support",
                "search_key": "SUPPORT_EMAIL",
                "valeur": "support@woila.app",
                "active": True
            },
            {
                "nom": "📱 Mode maintenance",
                "search_key": "MAINTENANCE_MODE",
                "valeur": "false",
                "active": False
            },
            {
                "nom": "🔐 Activation de la vérification OTP",
                "search_key": "ENABLE_OTP_VERIFICATION",
                "valeur": "true",
                "active": True
            },
            {
                "nom": "🚗 État minimum requis pour les véhicules",
                "search_key": "MIN_VEHICLE_STATE",
                "valeur": "6",
                "active": True
            }
        ]
        
        # Créer les configurations
        for config_data in default_configs:
            GeneralConfig.objects.create(**config_data)


def reverse_load_default_configs(apps, schema_editor):
    """
    Fonction de rollback - supprime toutes les configurations par défaut
    """
    GeneralConfig = apps.get_model('api', 'GeneralConfig')
    
    # Supprimer uniquement les configurations par défaut
    default_keys = [
        "MAX_WAITING_TIME", "WELCOME_BONUS_AMOUNT", "MIN_RECHARGE_AMOUNT",
        "PLATFORM_COMMISSION_RATE", "SUPPORT_EMAIL", "MAINTENANCE_MODE",
        "ENABLE_OTP_VERIFICATION", "MIN_VEHICLE_STATE"
    ]
    
    GeneralConfig.objects.filter(search_key__in=default_keys).delete()


class Migration(migrations.Migration):
    """
    Migration pour charger automatiquement les configurations par défaut
    """

    dependencies = [
        ('api', '0008_alter_generalconfig_options'),
    ]

    operations = [
        migrations.RunPython(
            load_default_configs,
            reverse_load_default_configs,
            hints={'verbosity': 1}
        ),
    ]