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
    marque = models.CharField(max_length=50, verbose_name="Marque")
    nom = models.CharField(max_length=100, verbose_name="Nom du véhicule")
    modele = models.CharField(max_length=50, verbose_name="Modèle")
    couleur = models.CharField(max_length=30, verbose_name="Couleur")
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
        return f"{self.marque} {self.nom} - {self.plaque_immatriculation} ({self.get_driver_info()})"
    
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
