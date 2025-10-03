from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import datetime, timedelta
import uuid


class Token(models.Model):
    """
    Token d'authentification pour les utilisateurs (Drivers et Customers).
    Utilise GenericForeignKey pour une relation ORM correcte.
    """
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # Relation polymorphe vers UserDriver ou UserCustomer
    limit = models.Q(app_label='users', model='userdriver') | models.Q(app_label='users', model='usercustomer')
    user_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, limit_choices_to=limit)
    user_id = models.PositiveIntegerField()
    user = GenericForeignKey('user_type', 'user_id')

    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        try:
            user_name = f"{self.user.name} {self.user.surname}" if hasattr(self.user, 'name') else str(self.user)
            return f"Token - {user_name} ({self.user_type.model})"
        except:
            return f"Token {self.user_type.model} - {self.user_id}"

    class Meta:
        db_table = 'auth_tokens'
        verbose_name = 'Token'
        verbose_name_plural = 'Tokens'
        unique_together = ['user_type', 'user_id']


class OTPVerification(models.Model):
    USER_TYPE_CHOICES = [
        ('driver', 'Driver'),
        ('customer', 'Customer'),
    ]
    
    phone_number = models.CharField(max_length=15)
    otp_code = models.CharField(max_length=4)  # 4 chiffres pour compatibilité app
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def can_attempt(self):
        return self.attempts < 3 and not self.is_expired()
    
    def __str__(self):
        return f"OTP {self.phone_number} - {self.otp_code}"
    
    class Meta:
        db_table = 'otp_verifications'
        verbose_name = 'Vérification OTP'
        verbose_name_plural = 'Vérifications OTP'
        ordering = ['-created_at']


class ReferralCode(models.Model):
    from django.contrib.contenttypes.fields import GenericForeignKey
    from django.contrib.contenttypes.models import ContentType

    code = models.CharField(max_length=8, unique=True)
    user_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    user_id = models.PositiveIntegerField()
    user = GenericForeignKey('user_type', 'user_id')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    used_count = models.IntegerField(default=0)

    def __str__(self):
        return f"Code {self.code} - {self.user_type.model} {self.user_id}"

    class Meta:
        db_table = 'referral_codes'
        verbose_name = 'Code de parrainage'
        verbose_name_plural = 'Codes de parrainage'
        unique_together = ('user_type', 'user_id')