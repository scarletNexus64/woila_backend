from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import uuid


def profile_picture_upload_path(instance, filename):
    """
    Génère le chemin de stockage des photos de profil
    Format: profile_pictures/user_type/user_id/filename
    """
    user_type = 'driver' if isinstance(instance, UserDriver) else 'customer'
    return f'profile_pictures/{user_type}/{instance.id}/{filename}'


def document_upload_path(instance, filename):
    """
    Génère le chemin de stockage des documents
    Format: documents/user_type/user_id/document_name/filename
    """
    user_type_name = instance.user_type.model if hasattr(instance.user_type, 'model') else 'unknown'
    return f'documents/{user_type_name}/{instance.user_id}/{instance.document_name}/{filename}'


class UserDriver(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    phone_number = models.CharField(max_length=15, unique=True)
    password = models.CharField(max_length=128)
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    age = models.IntegerField()
    birthday = models.DateField()
    profile_picture = models.ImageField(
        upload_to=profile_picture_upload_path, 
        null=True, 
        blank=True,
        verbose_name="Photo de profil"
    )
    
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
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
    
    def get_profile_picture_url(self, request=None):
        """Retourne l'URL de la photo de profil"""
        if self.profile_picture:
            if request:
                return request.build_absolute_uri(self.profile_picture.url)
            return self.profile_picture.url
        return None
    
    def __str__(self):
        return f"{self.name} {self.surname} - {self.phone_number}"
    
    class Meta:
        db_table = 'user_drivers'
        verbose_name = 'Chauffeur'
        verbose_name_plural = 'Chauffeurs'


class UserCustomer(models.Model):
    phone_number = models.CharField(max_length=15, unique=True)
    password = models.CharField(max_length=128)
    name = models.CharField(max_length=100, blank=True, default='')
    surname = models.CharField(max_length=100, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
    
    def __str__(self):
        return f"Customer - {self.phone_number}"
    
    class Meta:
        db_table = 'user_customers'
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'


class Document(models.Model):
    """
    Document pour les utilisateurs (Drivers et Customers).
    Utilise GenericForeignKey pour une relation ORM correcte.
    """
    # Relation polymorphe vers UserDriver ou UserCustomer
    limit = models.Q(app_label='users', model='userdriver') | models.Q(app_label='users', model='usercustomer')
    user_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, limit_choices_to=limit, verbose_name="Type d'utilisateur")
    user_id = models.PositiveIntegerField(verbose_name="ID Utilisateur")
    user = GenericForeignKey('user_type', 'user_id')

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

    def get_file_url(self, request=None):
        """Retourne l'URL du fichier"""
        if self.file:
            if request:
                return request.build_absolute_uri(self.file.url)
            return self.file.url
        return None

    def get_file_size_display(self):
        """Retourne la taille du fichier formatée"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"

    def __str__(self):
        try:
            user_name = f"{self.user.name} {self.user.surname}" if hasattr(self.user, 'name') else str(self.user)
            return f"{self.document_name} - {user_name} ({self.user_type.model})"
        except:
            return f"{self.document_name} - {self.user_type.model} {self.user_id}"

    class Meta:
        db_table = 'documents'
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        ordering = ['-uploaded_at']