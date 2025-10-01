from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
import secrets
import uuid


def generate_transaction_reference():
    """Génère une référence unique pour les transactions"""
    return f"TXN-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


class Wallet(models.Model):
    """
    E-wallet for users (Drivers and Customers).
    """
    limit = models.Q(app_label='users', model='userdriver') | models.Q(app_label='users', model='usercustomer')
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


class WalletTransaction(models.Model):
    """
    Model pour les transactions de wallet (dépôts, retraits, etc.)
    """
    TRANSACTION_TYPES = [
        ('deposit', 'Dépôt'),
        ('withdrawal', 'Retrait'),
        ('transfer_in', 'Transfert entrant'),
        ('transfer_out', 'Transfert sortant'),
        ('refund', 'Remboursement'),
        ('payment', 'Paiement'),
    ]
    
    TRANSACTION_STATUS = [
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
        ('cancelled', 'Annulé'),
    ]
    
    PAYMENT_METHODS = [
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Virement bancaire'),
        ('cash', 'Espèces'),
        ('other', 'Autre'),
    ]
    
    # Référence unique de la transaction
    reference = models.CharField(
        max_length=50, 
        unique=True, 
        default=generate_transaction_reference,
        verbose_name="Référence",
        help_text="Référence unique de la transaction"
    )
    
    # Utilisateur propriétaire du wallet
    limit = models.Q(app_label='users', model='userdriver') | models.Q(app_label='users', model='usercustomer')
    user_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, limit_choices_to=limit)
    user_id = models.PositiveIntegerField()
    user = GenericForeignKey('user_type', 'user_id')
    
    # Détails de la transaction
    transaction_type = models.CharField(
        max_length=20, 
        choices=TRANSACTION_TYPES, 
        verbose_name="Type de transaction"
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Montant"
    )
    status = models.CharField(
        max_length=20, 
        choices=TRANSACTION_STATUS, 
        default='pending',
        verbose_name="Statut"
    )
    
    # Informations de paiement
    payment_method = models.CharField(
        max_length=20, 
        choices=PAYMENT_METHODS, 
        blank=True,
        verbose_name="Méthode de paiement"
    )
    phone_number = models.CharField(
        max_length=15, 
        blank=True,
        verbose_name="Numéro de téléphone",
        help_text="Numéro pour Mobile Money"
    )
    
    # Détails FreeMoPay
    freemopay_reference = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name="Référence FreeMoPay"
    )
    freemopay_external_id = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name="ID externe FreeMoPay"
    )
    
    # Soldes avant/après transaction
    balance_before = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        verbose_name="Solde avant"
    )
    balance_after = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        verbose_name="Solde après"
    )
    
    # Description et métadonnées
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name="Message d'erreur",
        help_text="Message d'erreur en cas d'échec de la transaction"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées",
        help_text="Données supplémentaires en JSON"
    )

    # Horodatage
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Complété le")
    
    def mark_as_completed(self):
        """Marque la transaction comme complétée"""
        if self.status != 'completed':
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.save(update_fields=['status', 'completed_at'])
    
    def mark_as_failed(self, reason=None):
        """Marque la transaction comme échouée"""
        if self.status != 'failed':
            self.status = 'failed'
            if reason:
                self.error_message = reason
            self.save(update_fields=['status', 'error_message'])
    
    def __str__(self):
        user_str = f"{self.user_type.model} {self.user_id}"
        return f"{self.reference} - {self.get_transaction_type_display()} - {self.amount} ({user_str})"
    
    class Meta:
        db_table = 'wallet_transactions'
        verbose_name = 'Transaction Wallet'
        verbose_name_plural = 'Transactions Wallet'
        ordering = ['-created_at']