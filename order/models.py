from django.db import models
from api.models import UserDriver, UserCustomer, VehicleType, City, VipZone
from django.core.exceptions import ValidationError
import uuid

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('ACCEPTED', 'Acceptée'),
        ('IN_PROGRESS', 'En cours'),
        ('COMPLETED', 'Terminée'),
        ('CANCELLED', 'Annulée'),
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
    vip_zone = models.ForeignKey(VipZone, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Zone VIP")
    
    # Distance et prix
    estimated_distance_km = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Distance estimée (km)")
    actual_distance_km = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Distance réelle (km)")
    
    base_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix de base")
    distance_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix distance")
    vehicle_additional_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Prix additionnel véhicule")
    city_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Prix ville")
    vip_zone_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Prix zone VIP")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix total")
    
    # Timing
    is_night_fare = models.BooleanField(default=False, verbose_name="Tarif nuit")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="Statut")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créée le")
    accepted_at = models.DateTimeField(null=True, blank=True, verbose_name="Acceptée le")
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="Démarrée le")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Terminée le")
    cancelled_at = models.DateTimeField(null=True, blank=True, verbose_name="Annulée le")
    
    # Notes
    customer_notes = models.TextField(blank=True, verbose_name="Notes client")
    driver_notes = models.TextField(blank=True, verbose_name="Notes chauffeur")
    cancellation_reason = models.TextField(blank=True, verbose_name="Raison d'annulation")
    
    def __str__(self):
        return f"Commande {self.id} - {self.customer} → {self.status}"
    
    class Meta:
        db_table = 'orders'
        verbose_name = 'Commande'
        verbose_name_plural = 'Commandes'
        ordering = ['-created_at']


class DriverStatus(models.Model):
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
    
    # Timestamps
    last_online = models.DateTimeField(null=True, blank=True, verbose_name="Dernière connexion")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")
    
    def __str__(self):
        return f"{self.driver} - {self.get_status_display()}"
    
    class Meta:
        db_table = 'driver_status'
        verbose_name = 'Statut Chauffeur'
        verbose_name_plural = 'Statuts Chauffeurs'


class OrderTracking(models.Model):
    EVENT_CHOICES = [
        ('ORDER_CREATED', 'Commande créée'),
        ('DRIVER_ASSIGNED', 'Chauffeur assigné'),
        ('DRIVER_ARRIVED', 'Chauffeur arrivé'),
        ('TRIP_STARTED', 'Course démarrée'),
        ('TRIP_COMPLETED', 'Course terminée'),
        ('ORDER_CANCELLED', 'Commande annulée'),
        ('LOCATION_UPDATE', 'MAJ position'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='tracking_events')
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES, verbose_name="Type d'événement")
    
    # Position au moment de l'événement
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    
    # Données additionnelles
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Métadonnées")
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    
    def __str__(self):
        return f"{self.order.id} - {self.get_event_type_display()}"
    
    class Meta:
        db_table = 'order_tracking'
        verbose_name = 'Suivi Commande'
        verbose_name_plural = 'Suivi Commandes'
        ordering = ['-created_at']
