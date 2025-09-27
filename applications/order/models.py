from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from applications.users.models import UserDriver, UserCustomer
from applications.vehicles.models import VehicleType
from core.models import City
from core.admin import VipZoneProxy
import uuid


class PaymentMethod(models.Model):
    """Types de paiement disponibles dans le système"""
    PAYMENT_TYPES = [
        ('CASH', 'Espèces'),
        ('OM', 'Orange Money'),
        ('MOMO', 'MTN Mobile Money'),
        ('WALLET', 'Portefeuille'),
    ]
    
    type = models.CharField(
        max_length=20, 
        choices=PAYMENT_TYPES, 
        unique=True,
        verbose_name="Type de paiement"
    )
    name = models.CharField(max_length=100, verbose_name="Nom affiché")
    description = models.TextField(blank=True, verbose_name="Description")
    icon = models.CharField(max_length=255, blank=True, verbose_name="Icône")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    min_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Montant minimum"
    )
    max_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Montant maximum"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
    
    class Meta:
        db_table = 'payment_methods'
        verbose_name = 'Méthode de paiement'
        verbose_name_plural = 'Méthodes de paiement'
        ordering = ['name']


class Order(models.Model):
    """Modèle principal pour les commandes de VTC"""
    STATUS_CHOICES = [
        ('DRAFT', 'Brouillon'),
        ('PENDING', 'En attente'),
        ('ACCEPTED', 'Acceptée'),
        ('DRIVER_ARRIVED', 'Chauffeur arrivé'),
        ('IN_PROGRESS', 'En cours'),
        ('COMPLETED', 'Terminée'),
        ('CANCELLED', 'Annulée'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('PROCESSING', 'En traitement'),
        ('PAID', 'Payé'),
        ('FAILED', 'Échoué'),
        ('REFUNDED', 'Remboursé'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(UserCustomer, on_delete=models.CASCADE, related_name='orders')
    driver = models.ForeignKey(UserDriver, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    
    # Informations de la course
    pickup_address = models.TextField(verbose_name="Adresse de départ")
    pickup_latitude = models.DecimalField(max_digits=10, decimal_places=8, verbose_name="Latitude départ")
    pickup_longitude = models.DecimalField(max_digits=11, decimal_places=8, verbose_name="Longitude départ")
    
    destination_address = models.TextField(verbose_name="Adresse de destination")
    destination_latitude = models.DecimalField(max_digits=10, decimal_places=8, verbose_name="Latitude destination")
    destination_longitude = models.DecimalField(max_digits=11, decimal_places=8, verbose_name="Longitude destination")
    
    # Configuration de la commande
    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.CASCADE, verbose_name="Type de véhicule")
    city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name="Ville")
    vip_zone = models.ForeignKey(VipZoneProxy, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Zone VIP")
    
    # Paiement
    payment_method = models.ForeignKey(
        PaymentMethod, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Méthode de paiement"
    )
    payment_status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS_CHOICES, 
        default='PENDING',
        verbose_name="Statut du paiement"
    )
    
    # Distance et prix
    estimated_distance_km = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Distance estimée (km)")
    actual_distance_km = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Distance réelle (km)")
    
    base_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix de base")
    distance_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix distance")
    vehicle_additional_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Prix additionnel véhicule")
    city_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Prix ville")
    vip_zone_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Prix zone VIP")
    waiting_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Prix attente")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix total estimé")
    final_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Prix final ajusté"
    )
    
    # Temps d'attente
    waiting_time = models.IntegerField(
        default=0,
        verbose_name="Temps d'attente (minutes)",
        help_text="Temps d'attente du client après l'arrivée du chauffeur"
    )
    
    # Ratings
    driver_rating = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Note du chauffeur (1-5)"
    )
    customer_rating = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Note du client (1-5)"
    )
    
    # Timing
    is_night_fare = models.BooleanField(default=False, verbose_name="Tarif nuit")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name="Statut")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créée le")
    accepted_at = models.DateTimeField(null=True, blank=True, verbose_name="Acceptée le")
    driver_arrived_at = models.DateTimeField(null=True, blank=True, verbose_name="Chauffeur arrivé le")
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="Démarrée le")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Terminée le")
    cancelled_at = models.DateTimeField(null=True, blank=True, verbose_name="Annulée le")
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="Payée le")
    
    # Notes
    customer_notes = models.TextField(blank=True, verbose_name="Notes client")
    driver_notes = models.TextField(blank=True, verbose_name="Notes chauffeur")
    cancellation_reason = models.TextField(blank=True, verbose_name="Raison d'annulation")
    
    def calculate_final_price(self):
        """Calcule le prix final basé sur la distance réelle et le temps d'attente"""
        if self.actual_distance_km:
            # Recalculer avec la distance réelle
            from .services import PricingService
            service = PricingService()
            pricing = service.calculate_order_price(
                vehicle_type_id=self.vehicle_type_id,
                city_id=self.city_id,
                distance_km=float(self.actual_distance_km),
                vip_zone_id=self.vip_zone_id if self.vip_zone else None,
                is_night=self.is_night_fare
            )
            # Ajouter le prix d'attente
            waiting_price = self.waiting_time * service._get_config_value('PRICE_PER_WAITING_MINUTE', 50)
            self.final_price = pricing['total_price'] + waiting_price
            self.waiting_price = waiting_price
        return self.final_price
    
    def __str__(self):
        return f"Commande {self.id} - {self.customer} → {self.status}"
    
    class Meta:
        db_table = 'orders'
        verbose_name = 'Commande'
        verbose_name_plural = 'Commandes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['customer']),
            models.Index(fields=['driver']),
        ]


class Rating(models.Model):
    """Système de notation bidirectionnel pour les courses"""
    RATING_TYPE_CHOICES = [
        ('DRIVER_TO_CUSTOMER', 'Chauffeur → Client'),
        ('CUSTOMER_TO_DRIVER', 'Client → Chauffeur'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='ratings')
    rating_type = models.CharField(max_length=20, choices=RATING_TYPE_CHOICES, verbose_name="Type de notation")
    
    # Qui note qui
    rater = models.ForeignKey(UserDriver, on_delete=models.CASCADE, null=True, blank=True, related_name='ratings_given')
    rated_driver = models.ForeignKey(UserDriver, on_delete=models.CASCADE, null=True, blank=True, related_name='ratings_received')
    rated_customer = models.ForeignKey(UserCustomer, on_delete=models.CASCADE, null=True, blank=True, related_name='ratings_received')
    
    # Note et feedback
    score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Note (1-5 étoiles)"
    )
    comment = models.TextField(blank=True, verbose_name="Commentaire")
    
    # Critères détaillés (optionnel)
    punctuality = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Ponctualité"
    )
    driving_quality = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Qualité de conduite"
    )
    vehicle_cleanliness = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Propreté du véhicule"
    )
    communication = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Communication"
    )
    
    # Tags prédéfinis
    tags = models.JSONField(
        default=list, 
        blank=True,
        verbose_name="Tags",
        help_text="Ex: ['Ponctuel', 'Véhicule propre', 'Conduite sûre']"
    )
    
    is_anonymous = models.BooleanField(default=False, verbose_name="Note anonyme")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")
    
    def clean(self):
        """Validation pour s'assurer que les bonnes relations sont définies"""
        if self.rating_type == 'DRIVER_TO_CUSTOMER':
            if not self.rater or not self.rated_customer:
                raise ValidationError("Pour une notation chauffeur→client, rater et rated_customer sont requis")
            if self.rated_driver:
                raise ValidationError("rated_driver ne doit pas être défini pour une notation chauffeur→client")
        elif self.rating_type == 'CUSTOMER_TO_DRIVER':
            if not self.rated_driver:
                raise ValidationError("Pour une notation client→chauffeur, rated_driver est requis")
            if self.rater or self.rated_customer:
                raise ValidationError("rater et rated_customer ne doivent pas être définis pour une notation client→chauffeur")
    
    def __str__(self):
        if self.rating_type == 'DRIVER_TO_CUSTOMER':
            return f"Note {self.score}/5 - {self.rater} → {self.rated_customer}"
        else:
            return f"Note {self.score}/5 - Client → {self.rated_driver}"
    
    class Meta:
        db_table = 'ratings'
        verbose_name = 'Notation'
        verbose_name_plural = 'Notations'
        ordering = ['-created_at']
        unique_together = [['order', 'rating_type']]


class TripTracking(models.Model):
    """Historique des positions GPS pendant une course"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='trip_tracking')
    driver = models.ForeignKey(UserDriver, on_delete=models.CASCADE, related_name='trip_tracking')
    
    # Position
    latitude = models.DecimalField(max_digits=10, decimal_places=8, verbose_name="Latitude")
    longitude = models.DecimalField(max_digits=11, decimal_places=8, verbose_name="Longitude")
    
    # Données additionnelles
    speed_kmh = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Vitesse (km/h)"
    )
    heading = models.IntegerField(
        null=True, 
        blank=True,
        verbose_name="Direction (0-359°)"
    )
    accuracy = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Précision GPS (mètres)"
    )
    
    # Statut au moment de l'enregistrement
    order_status = models.CharField(
        max_length=20, 
        choices=Order.STATUS_CHOICES,
        verbose_name="Statut de la commande"
    )
    
    recorded_at = models.DateTimeField(auto_now_add=True, verbose_name="Enregistré le")
    
    def __str__(self):
        return f"Tracking {self.order.id} - {self.recorded_at}"
    
    class Meta:
        db_table = 'trip_tracking'
        verbose_name = 'Suivi GPS'
        verbose_name_plural = 'Suivis GPS'
        ordering = ['order', 'recorded_at']
        indexes = [
            models.Index(fields=['order', 'recorded_at']),
            models.Index(fields=['latitude', 'longitude']),
        ]


class DriverPool(models.Model):
    """Gestion du pool de chauffeurs pour une commande"""
    RESPONSE_STATUS = [
        ('PENDING', 'En attente'),
        ('ACCEPTED', 'Accepté'),
        ('REJECTED', 'Refusé'),
        ('TIMEOUT', 'Timeout'),
        ('CANCELLED', 'Annulé'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='driver_pool')
    driver = models.ForeignKey(UserDriver, on_delete=models.CASCADE, related_name='pool_requests')
    
    # Ordre et timing
    priority_order = models.IntegerField(
        verbose_name="Ordre de priorité",
        help_text="1 = premier appelé, 2 = deuxième, etc."
    )
    distance_km = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        verbose_name="Distance du client (km)"
    )
    
    # Statut de la requête
    request_status = models.CharField(
        max_length=20, 
        choices=RESPONSE_STATUS, 
        default='PENDING',
        verbose_name="Statut de la requête"
    )
    
    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True, verbose_name="Demandé le")
    responded_at = models.DateTimeField(null=True, blank=True, verbose_name="Répondu le")
    timeout_at = models.DateTimeField(verbose_name="Timeout le")
    
    # Réponse
    response_time_seconds = models.IntegerField(
        null=True, 
        blank=True,
        verbose_name="Temps de réponse (secondes)"
    )
    rejection_reason = models.CharField(
        max_length=255, 
        blank=True,
        verbose_name="Raison du refus"
    )
    
    def save(self, *args, **kwargs):
        """Calcule le temps de réponse et le timeout"""
        if not self.timeout_at:
            from django.conf import settings
            from datetime import timedelta
            max_wait = getattr(settings, 'MAX_DRIVER_WAITING_TIME', 30)
            self.timeout_at = timezone.now() + timedelta(seconds=max_wait)
        
        if self.responded_at and self.requested_at:
            delta = self.responded_at - self.requested_at
            self.response_time_seconds = int(delta.total_seconds())
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Pool {self.order.id} - {self.driver} (#{self.priority_order})"
    
    class Meta:
        db_table = 'driver_pool'
        verbose_name = 'Pool Chauffeur'
        verbose_name_plural = 'Pool Chauffeurs'
        ordering = ['order', 'priority_order']
        unique_together = [['order', 'driver']]
        indexes = [
            models.Index(fields=['order', 'priority_order']),
            models.Index(fields=['request_status']),
        ]


class DriverStatus(models.Model):
    """Statut en temps réel des chauffeurs"""
    STATUS_CHOICES = [
        ('OFFLINE', 'Hors ligne'),
        ('ONLINE', 'En ligne'),
        ('BUSY', 'Occupé'),
    ]
    
    driver = models.OneToOneField(UserDriver, on_delete=models.CASCADE, related_name='status')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OFFLINE', verbose_name="Statut")
    
    # Position actuelle
    current_latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True, verbose_name="Latitude actuelle")
    current_longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True, verbose_name="Longitude actuelle")
    last_location_update = models.DateTimeField(null=True, blank=True, verbose_name="Dernière MAJ position")
    
    # WebSocket
    websocket_channel = models.CharField(max_length=255, null=True, blank=True, verbose_name="Canal WebSocket")
    
    # Statistiques de la session
    session_started_at = models.DateTimeField(null=True, blank=True, verbose_name="Session démarrée le")
    total_orders_today = models.IntegerField(default=0, verbose_name="Commandes aujourd'hui")
    total_earnings_today = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Gains aujourd'hui"
    )
    
    # Timestamps
    last_online = models.DateTimeField(null=True, blank=True, verbose_name="Dernière connexion")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")
    
    def go_online(self):
        """Passe le chauffeur en ligne"""
        self.status = 'ONLINE'
        self.last_online = timezone.now()
        self.session_started_at = timezone.now()
        self.save()
    
    def go_offline(self):
        """Passe le chauffeur hors ligne"""
        self.status = 'OFFLINE'
        self.session_started_at = None
        self.save()
    
    def __str__(self):
        return f"{self.driver} - {self.get_status_display()}"
    
    class Meta:
        db_table = 'driver_status'
        verbose_name = 'Statut Chauffeur'
        verbose_name_plural = 'Statuts Chauffeurs'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['current_latitude', 'current_longitude']),
        ]


class CustomerStatus(models.Model):
    """Statut en temps réel des clients pendant les commandes"""
    
    customer = models.OneToOneField(UserCustomer, on_delete=models.CASCADE, related_name='status')
    
    # Position actuelle
    current_latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True, verbose_name="Latitude actuelle")
    current_longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True, verbose_name="Longitude actuelle")
    last_location_update = models.DateTimeField(null=True, blank=True, verbose_name="Dernière MAJ position")
    
    # Commande active
    current_order = models.ForeignKey(
        Order, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='customer_tracking',
        verbose_name="Commande active"
    )
    
    # WebSocket
    websocket_channel = models.CharField(max_length=255, null=True, blank=True, verbose_name="Canal WebSocket")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")
    
    def __str__(self):
        return f"{self.customer} - Position tracking"
    
    class Meta:
        db_table = 'customer_status'
        verbose_name = 'Statut Client'
        verbose_name_plural = 'Statuts Clients'
        indexes = [
            models.Index(fields=['current_latitude', 'current_longitude']),
            models.Index(fields=['current_order']),
        ]


class OrderTracking(models.Model):
    """Événements de suivi d'une commande"""
    EVENT_CHOICES = [
        ('ORDER_CREATED', 'Commande créée'),
        ('DRIVER_SEARCH_STARTED', 'Recherche chauffeur démarrée'),
        ('DRIVER_NOTIFIED', 'Chauffeur notifié'),
        ('DRIVER_ACCEPTED', 'Chauffeur a accepté'),
        ('DRIVER_REJECTED', 'Chauffeur a refusé'),
        ('DRIVER_ASSIGNED', 'Chauffeur assigné'),
        ('DRIVER_EN_ROUTE', 'Chauffeur en route'),
        ('DRIVER_ARRIVED', 'Chauffeur arrivé'),
        ('TRIP_STARTED', 'Course démarrée'),
        ('TRIP_COMPLETED', 'Course terminée'),
        ('ORDER_CANCELLED', 'Commande annulée'),
        ('PAYMENT_INITIATED', 'Paiement initié'),
        ('PAYMENT_COMPLETED', 'Paiement complété'),
        ('PAYMENT_FAILED', 'Paiement échoué'),
        ('RATING_SUBMITTED', 'Note soumise'),
        ('LOCATION_UPDATE', 'MAJ position'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='tracking_events')
    event_type = models.CharField(max_length=30, choices=EVENT_CHOICES, verbose_name="Type d'événement")
    
    # Acteur de l'événement
    driver = models.ForeignKey(UserDriver, on_delete=models.SET_NULL, null=True, blank=True)
    customer = models.ForeignKey(UserCustomer, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Position au moment de l'événement
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    
    # Données additionnelles
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Métadonnées")
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    
    def __str__(self):
        return f"{self.order.id} - {self.get_event_type_display()} - {self.created_at}"
    
    class Meta:
        db_table = 'order_tracking'
        verbose_name = 'Suivi Commande'
        verbose_name_plural = 'Suivi Commandes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order', '-created_at']),
            models.Index(fields=['event_type']),
        ]
