from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone


class NotificationConfig(models.Model):
    """Configuration pour les notifications d'OTP"""
    CHANNEL_CHOICES = [
        ('sms', 'SMS (Nexah)'),
        ('whatsapp', 'WhatsApp (Meta)')
    ]
    
    default_channel = models.CharField(
        max_length=20, 
        choices=CHANNEL_CHOICES,
        default='sms',
        verbose_name="Canal de notification par défaut"
    )
    
    # SMS Nexah settings
    nexah_base_url = models.CharField(
        max_length=255,
        default='https://api.nexah.net/',
        verbose_name="URL de base Nexah"
    )
    nexah_send_endpoint = models.CharField(
        max_length=100,
        default='api/bulk/send',
        verbose_name="Endpoint d'envoi Nexah"
    )
    nexah_credits_endpoint = models.CharField(
        max_length=100,
        default='api/credits',
        verbose_name="Endpoint de crédits Nexah"
    )
    nexah_user = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name="Utilisateur Nexah"
    )
    nexah_password = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name="Mot de passe Nexah"
    )
    nexah_sender_id = models.CharField(
        max_length=20, 
        default='WOILA',
        verbose_name="ID expéditeur Nexah"
    )
    
    # WhatsApp settings
    whatsapp_api_token = models.TextField(
        blank=True,
        verbose_name="Token API WhatsApp",
        help_text="Token permanent pour l'API WhatsApp"
    )
    whatsapp_phone_number_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="ID du numéro WhatsApp"
    )
    whatsapp_business_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="ID Business WhatsApp"
    )
    
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Configuration OTP - Canal: {self.get_default_channel_display()}"
    
    class Meta:
        db_table = 'notification_configs'
        verbose_name = 'Configuration de notification'
        verbose_name_plural = 'Configurations de notification'


class Notification(models.Model):
    """
    Model pour stocker les notifications des utilisateurs (chauffeurs et clients)
    """
    NOTIFICATION_TYPES = [
        ('welcome', 'Notification de bienvenue'),
        ('referral_used', 'Code parrain utilisé'),
        ('vehicle_approved', 'Véhicule approuvé'),
        ('system', 'Notification système'),
        ('order', 'Commande'),
        ('other', 'Autre'),
    ]
    
    # Utilisateur qui recoit la notification (Generic Foreign Key)
    limit = models.Q(app_label='users', model='userdriver') | models.Q(app_label='users', model='usercustomer')
    user_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, limit_choices_to=limit)
    user_id = models.PositiveIntegerField()
    user = GenericForeignKey('user_type', 'user_id')
    
    # Contenu de la notification
    title = models.CharField(max_length=200, verbose_name="Titre")
    content = models.TextField(verbose_name="Contenu")
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='system',
        verbose_name="Type de notification"
    )
    
    # Statuts de lecture
    is_read = models.BooleanField(default=False, verbose_name="Lu")
    is_deleted = models.BooleanField(default=False, verbose_name="Supprimé")
    
    # Métadonnées supplémentaires (JSON pour flexibilité)
    try:
        from django.db.models import JSONField
    except ImportError:
        from django.contrib.postgres.fields import JSONField
    
    metadata = JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées",
        help_text="Données supplémentaires (code parrain, ID véhicule, etc.)"
    )
    
    # Horodatage
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Lu le")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Supprimé le")
    
    def mark_as_read(self):
        """Marque la notification comme lue"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def soft_delete(self):
        """Suppression douce de la notification"""
        if not self.is_deleted:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save(update_fields=['is_deleted', 'deleted_at'])
    
    def __str__(self):
        user_str = f"{self.user_type.model} {self.user_id}"
        return f"{self.title} - {user_str}"
    
    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']


class FCMToken(models.Model):
    """
    Modèle pour stocker les tokens FCM des utilisateurs
    """
    # Utilisateur qui possède ce token (Generic Foreign Key)  
    limit = models.Q(app_label='users', model='userdriver') | models.Q(app_label='users', model='usercustomer')
    user_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, limit_choices_to=limit)
    user_id = models.PositiveIntegerField()
    user = GenericForeignKey('user_type', 'user_id')
    
    # Token FCM
    token = models.TextField(verbose_name="Token FCM", unique=True)
    
    # Informations sur l'appareil
    platform = models.CharField(
        max_length=20, 
        verbose_name="Plateforme",
        help_text="android, ios, web, etc."
    )
    device_id = models.CharField(
        max_length=255,
        verbose_name="ID de l'appareil",
        help_text="Identifiant unique de l'appareil"
    )
    device_info = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Informations appareil",
        help_text="Version OS, modèle, etc."
    )
    
    # Statut du token
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    last_used = models.DateTimeField(null=True, blank=True, verbose_name="Dernière utilisation")
    
    # Horodatage
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    def update_last_used(self):
        """Met à jour la dernière utilisation du token"""
        self.last_used = timezone.now()
        self.save(update_fields=['last_used'])
    
    def deactivate(self):
        """Désactive le token"""
        self.is_active = False
        self.save(update_fields=['is_active'])
    
    def __str__(self):
        user_str = f"{self.user_type.model} {self.user_id}"
        return f"FCM Token - {user_str} ({self.platform})"
    
    class Meta:
        db_table = 'fcm_tokens'
        verbose_name = 'Token FCM'
        verbose_name_plural = 'Tokens FCM'
        ordering = ['-created_at']
        unique_together = ('user_type', 'user_id', 'device_id')