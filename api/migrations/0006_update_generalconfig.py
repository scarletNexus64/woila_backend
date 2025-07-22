# Generated manually to update GeneralConfig model

from django.db import migrations, models
from django.utils import timezone


def migrate_old_data(apps, schema_editor):
    """
    Migre les anciennes données vers le nouveau format
    """
    pass  # Pour l'instant on laisse vide, on ajoutera des configs exemple après


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_generalconfig_referralcode_wallet'),
    ]

    operations = [
        # Ajouter les nouveaux champs avec des valeurs par défaut
        migrations.AddField(
            model_name='generalconfig',
            name='nom',
            field=models.CharField(default='Configuration par défaut', max_length=100, verbose_name='Nom de la configuration'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='generalconfig',
            name='search_key',
            field=models.CharField(default='DEFAULT_CONFIG', max_length=100, unique=True, verbose_name='Clé de recherche'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='generalconfig',
            name='valeur',
            field=models.TextField(default='0', help_text='Valeur de la configuration (peut être castée en nombre si nécessaire)', verbose_name='Valeur'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='generalconfig',
            name='active',
            field=models.BooleanField(default=True, verbose_name='Actif'),
        ),
        migrations.AddField(
            model_name='generalconfig',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=timezone.now, verbose_name='Date de création'),
            preserve_default=False,
        ),
        
        # Supprimer l'ancien champ
        migrations.RemoveField(
            model_name='generalconfig',
            name='referral_bonus_amount',
        ),
        
        # Modifier la table pour utiliser le nouveau nom
        migrations.AlterModelTable(
            name='generalconfig',
            table='general_configs',
        ),
        
        # Modifier les options du modèle
        migrations.AlterModelOptions(
            name='generalconfig',
            options={'ordering': ['nom'], 'verbose_name': 'Configuration Générale', 'verbose_name_plural': 'Configurations'},
        ),
        
        # Exécuter la migration des données
        migrations.RunPython(migrate_old_data),
    ]