from django.db import models
from django.contrib.auth.hashers import make_password, check_password
import uuid
from datetime import datetime
import os

class UserDriver(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    phone_number = models.CharField(max_length=15, unique=True)
    password = models.CharField(max_length=128)
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    age = models.IntegerField()
    birthday = models.DateField()
    
    # Champs partenaires
    is_partenaire_interne = models.BooleanField(default=False, verbose_name="Partenaire Interne")
    is_partenaire_externe = models.BooleanField(default=False, verbose_name="Partenaire Externe")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    def __str__(self):
        return f"{self.name} {self.surname} - {self.phone_number}"
    
    class Meta:
        db_table = 'user_drivers'
        verbose_name = 'Chauffeur'
        verbose_name_plural = 'Chauffeurs'


class UserCustomer(models.Model):
    phone_number = models.CharField(max_length=15, unique=True)
    password = models.CharField(max_length=128)
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    def __str__(self):
        return f"{self.name} {self.surname} - {self.phone_number}"
    
    class Meta:
        db_table = 'user_customers'
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'


class Token(models.Model):
    USER_TYPE_CHOICES = [
        ('driver', 'Driver'),
        ('customer', 'Customer'),
    ]
    
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    user_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Token {self.user_type} - {self.user_id}"
    
    class Meta:
        db_table = 'auth_tokens'
        verbose_name = 'Token'
        verbose_name_plural = 'Tokens'


def document_upload_path(instance, filename):
    """
    Génère le chemin de stockage des documents
    Format: documents/user_type/user_id/document_name/filename
    """
    return f'documents/{instance.user_type}/{instance.user_id}/{instance.document_name}/{filename}'


class Document(models.Model):
    USER_TYPE_CHOICES = [
        ('driver', 'Chauffeur'),
        ('customer', 'Client'),
    ]
    
    user_id = models.IntegerField(verbose_name="ID Utilisateur")
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, verbose_name="Type d'utilisateur")
    document_name = models.CharField(max_length=100, verbose_name="Nom du document")
    file = models.FileField(upload_to=document_upload_path, verbose_name="Fichier")
    original_filename = models.CharField(max_length=255, verbose_name="Nom du fichier original")
    file_size = models.IntegerField(verbose_name="Taille du fichier (bytes)")
    content_type = models.CharField(max_length=100, verbose_name="Type de contenu")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'import")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    
    def save(self, *args, **kwargs):
        if self.file:
            self.original_filename = self.file.name
            self.file_size = self.file.size
            self.content_type = getattr(self.file, 'content_type', 'application/octet-stream')
        super().save(*args, **kwargs)
    
    def get_user_info(self):
        """Récupère les informations de l'utilisateur associé"""
        if self.user_type == 'driver':
            try:
                user = UserDriver.objects.get(id=self.user_id)
                return f"{user.name} {user.surname} ({user.phone_number})"
            except UserDriver.DoesNotExist:
                return f"Chauffeur ID {self.user_id} (supprimé)"
        else:
            try:
                user = UserCustomer.objects.get(id=self.user_id)
                return f"{user.name} {user.surname} ({user.phone_number})"
            except UserCustomer.DoesNotExist:
                return f"Client ID {self.user_id} (supprimé)"
    
    def __str__(self):
        return f"{self.document_name} - {self.get_user_info()}"
    
    class Meta:
        db_table = 'documents'
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        ordering = ['-uploaded_at']


def vehicle_image_upload_path(instance, filename):
    """
    Génère le chemin de stockage des images de véhicules
    Format: vehicles/driver_id/vehicle_id/filename
    """
    return f'vehicles/{instance.driver_id}/{instance.id or "temp"}/{filename}'


class VehicleType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom du type")
    additional_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Montant additionnel"
    )
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'vehicle_types'
        verbose_name = 'Type de véhicule'
        verbose_name_plural = 'Types de véhicule'


class VehicleBrand(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom de la marque")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'vehicle_brands'
        verbose_name = 'Marque de véhicule'
        verbose_name_plural = 'Marques de véhicule'


class VehicleModel(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom du modèle")
    brand = models.ForeignKey(
        VehicleBrand,
        on_delete=models.CASCADE,
        related_name='models',
        verbose_name="Marque"
    )
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    def __str__(self):
        return f"{self.brand.name} {self.name}"

    class Meta:
        db_table = 'vehicle_models'
        verbose_name = 'Modèle de véhicule'
        verbose_name_plural = 'Modèles de véhicule'
        unique_together = ('brand', 'name')


class VehicleColor(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Nom de la couleur")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'vehicle_colors'
        verbose_name = 'Couleur de véhicule'
        verbose_name_plural = 'Couleurs de véhicule'


class Vehicle(models.Model):
    ETAT_CHOICES = [
        (1, '1 - Très mauvais état'),
        (2, '2 - Mauvais état'),
        (3, '3 - État passable'),
        (4, '4 - État correct'),
        (5, '5 - État moyen'),
        (6, '6 - Bon état'),
        (7, '7 - Très bon état'),
        (8, '8 - Excellent état'),
        (9, '9 - État quasi neuf'),
        (10, '10 - État neuf'),
    ]

    driver = models.ForeignKey(
        UserDriver,
        on_delete=models.CASCADE,
        related_name='vehicles',
        verbose_name="Chauffeur"
    )
    vehicle_type = models.ForeignKey(
        VehicleType,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Type de véhicule"
    )
    brand = models.ForeignKey(
        VehicleBrand,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Marque"
    )
    model = models.ForeignKey(
        VehicleModel,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Modèle"
    )
    color = models.ForeignKey(
        VehicleColor,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Couleur"
    )
    nom = models.CharField(max_length=100, verbose_name="Nom du véhicule")
    plaque_immatriculation = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Plaque d'immatriculation"
    )
    etat_vehicule = models.IntegerField(
        choices=ETAT_CHOICES,
        verbose_name="État du véhicule (1-10)"
    )

    # Images du véhicule
    photo_exterieur_1 = models.ImageField(
        upload_to=vehicle_image_upload_path,
        verbose_name="Photo extérieure 1",
        blank=True,
        null=True
    )
    photo_exterieur_2 = models.ImageField(
        upload_to=vehicle_image_upload_path,
        verbose_name="Photo extérieure 2",
        blank=True,
        null=True
    )
    photo_interieur_1 = models.ImageField(
        upload_to=vehicle_image_upload_path,
        verbose_name="Photo intérieure 1",
        blank=True,
        null=True
    )
    photo_interieur_2 = models.ImageField(
        upload_to=vehicle_image_upload_path,
        verbose_name="Photo intérieure 2",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    def get_etat_display_short(self):
        """Retourne l'état sous forme courte"""
        return f"{self.etat_vehicule}/10"

    def get_driver_info(self):
        """Retourne les infos du chauffeur"""
        return f"{self.driver.name} {self.driver.surname} ({self.driver.phone_number})"

    def get_images_urls(self, request=None):
        """Retourne les URLs des images"""
        images = {}
        for field in ['photo_exterieur_1', 'photo_exterieur_2', 'photo_interieur_1', 'photo_interieur_2']:
            image = getattr(self, field)
            if image and request:
                images[field] = request.build_absolute_uri(image.url)
            elif image:
                images[field] = image.url
            else:
                images[field] = None
        return images

    def __str__(self):
        return f"{self.brand} {self.model} - {self.plaque_immatriculation} ({self.get_driver_info()})"
    
    class Meta:
        db_table = 'vehicles'
        verbose_name = 'Véhicule'
        verbose_name_plural = 'Véhicules'
        ordering = ['-created_at']


# Models for referral system
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
import secrets

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


class Wallet(models.Model):
    """
    E-wallet for users (Drivers and Customers).
    """
    limit = models.Q(app_label='api', model='userdriver') | models.Q(app_label='api', model='usercustomer')
    user_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, limit_choices_to=limit)
    user_id = models.PositiveIntegerField()
    user = GenericForeignKey('user_type', 'user_id')

    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Solde"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Portefeuille de {self.user} - Solde: {self.balance}"

    class Meta:
        db_table = 'wallets'
        verbose_name = 'Portefeuille'
        verbose_name_plural = 'Portefeuilles'
        unique_together = ('user_type', 'user_id')


def generate_referral_code():
    """Generates a unique referral code."""
    return secrets.token_hex(4).upper()

class ReferralCode(models.Model):
    """
    Unique referral code for each user.
    """
    limit = models.Q(app_label='api', model='userdriver') | models.Q(app_label='api', model='usercustomer')
    user_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, limit_choices_to=limit)
    user_id = models.PositiveIntegerField()
    user = GenericForeignKey('user_type', 'user_id')

    code = models.CharField(
        max_length=8,
        unique=True,
        default=generate_referral_code,
        verbose_name="Code de parrainage"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Code {self.code} pour {self.user}"

    class Meta:
        db_table = 'referral_codes'
        verbose_name = 'Code de parrainage'
        verbose_name_plural = 'Codes de parrainage'
        unique_together = ('user_type', 'user_id')


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
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom de la zone VIP")
    prix_jour = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Prix de base jour (FCFA)"
    )
    prix_nuit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Prix de base nuit (FCFA)"
    )
    active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    def __str__(self):
        return f"Zone VIP: {self.name}"

    class Meta:
        db_table = 'vip_zones'
        verbose_name = '👑 Zone VIP'
        verbose_name_plural = '👑 Zones VIP'
        ordering = ['name']


class VipZoneKilometerRule(models.Model):
    vip_zone = models.ForeignKey(
        VipZone,
        on_delete=models.CASCADE,
        related_name='kilometer_rules',
        verbose_name="Zone VIP"
    )
    min_kilometers = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Kilométrage minimum",
        help_text="À partir de combien de km cette règle s'applique"
    )
    prix_jour_per_km = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Prix par km (jour)",
        help_text="Prix par kilomètre supplémentaire en journée"
    )
    prix_nuit_per_km = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Prix par km (nuit)",
        help_text="Prix par kilomètre supplémentaire la nuit"
    )
    active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    def __str__(self):
        return f"{self.vip_zone.name} - À partir de {self.min_kilometers}km"

    class Meta:
        db_table = 'vip_zone_kilometer_rules'
        verbose_name = '📏 Règle KM'
        verbose_name_plural = '📏 Règles KM'
        ordering = ['vip_zone', 'min_kilometers']
        unique_together = ('vip_zone', 'min_kilometers')
