from django.db import models


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

    # Note: We'll import UserDriver from users.models after migration is complete
    driver = models.ForeignKey(
        'users.UserDriver',
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
    is_active = models.BooleanField(default=False, verbose_name="Actif")
    is_online = models.BooleanField(default=False, verbose_name="En service")

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