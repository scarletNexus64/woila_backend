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
