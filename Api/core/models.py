from django.db import models


class GeneralConfig(models.Model):
    """
    Model pour les configurations générales de l'application.
    Chaque configuration a un nom, une clé de recherche, une valeur et un statut actif.
    """
    nom = models.CharField(
        max_length=100,
        verbose_name="Nom de la configuration"
    )
    search_key = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Clé de recherche"
    )
    valeur = models.TextField(
        verbose_name="Valeur",
        help_text="Valeur de la configuration (peut être castée en nombre si nécessaire)"
    )
    active = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    def get_numeric_value(self):
        """
        Tente de convertir la valeur en nombre (float).
        Retourne None si la conversion échoue.
        """
        try:
            return float(self.valeur)
        except (ValueError, TypeError):
            return None

    def get_boolean_value(self):
        """
        Tente de convertir la valeur en booléen.
        """
        if self.valeur.lower() in ['true', '1', 'oui', 'yes', 'on']:
            return True
        elif self.valeur.lower() in ['false', '0', 'non', 'no', 'off']:
            return False
        return None

    def __str__(self):
        return f"{self.nom} ({self.search_key})"

    class Meta:
        db_table = 'general_configs'
        verbose_name = "Configuration Générale"
        verbose_name_plural = "Configurations"
        ordering = ['nom']


class Country(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom du pays")
    active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'countries'
        verbose_name = '🌍 Pays'
        verbose_name_plural = '🌍 Pays'
        ordering = ['name']


class City(models.Model):
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name='cities',
        verbose_name="Pays"
    )
    name = models.CharField(max_length=100, verbose_name="Nom de la ville")
    prix_jour = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Prix jour (FCFA)"
    )
    prix_nuit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Prix nuit (FCFA)"
    )
    active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    def __str__(self):
        return f"{self.name} ({self.country.name})"

    class Meta:
        db_table = 'cities'
        verbose_name = '🏙️ Ville'
        verbose_name_plural = '🏙️ Villes'
        ordering = ['country__name', 'name']
        unique_together = ('country', 'name')


class VipZone(models.Model):
    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name='vip_zones',
        verbose_name="Ville"
    )
    name = models.CharField(max_length=100, verbose_name="Nom de la zone VIP")
    additional_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Montant additionnel (FCFA)"
    )
    active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    def __str__(self):
        return f"{self.name} - {self.city.name}"

    class Meta:
        db_table = 'vip_zones'
        verbose_name = '⭐ Zone VIP'
        verbose_name_plural = '⭐ Zones VIP'
        ordering = ['city__name', 'name']
        unique_together = ('city', 'name')


class VipZoneKilometerRule(models.Model):
    vip_zone = models.ForeignKey(
        VipZone,
        on_delete=models.CASCADE,
        related_name='kilometer_rules',
        verbose_name="Zone VIP"
    )
    min_km = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Kilomètres minimum"
    )
    max_km = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Kilomètres maximum"
    )
    additional_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Montant additionnel (FCFA)"
    )
    active = models.BooleanField(default=True, verbose_name="Actif")

    def __str__(self):
        return f"{self.vip_zone.name} ({self.min_km}-{self.max_km}km): +{self.additional_amount}"

    class Meta:
        db_table = 'vip_zone_kilometer_rules'
        verbose_name = '📏 Règle kilométrique VIP'
        verbose_name_plural = '📏 Règles kilométriques VIP'
        ordering = ['vip_zone__name', 'min_km']