from rest_framework import serializers
from .models import Vehicle, VehicleType, VehicleBrand, VehicleModel, VehicleColor


class VehicleTypeSerializer(serializers.ModelSerializer):
    """Serializer pour les types de véhicules"""
    
    class Meta:
        model = VehicleType
        fields = ['id', 'name', 'additional_amount', 'is_active']
        read_only_fields = ['id']


class VehicleBrandSerializer(serializers.ModelSerializer):
    """Serializer pour les marques de véhicules"""
    
    class Meta:
        model = VehicleBrand
        fields = ['id', 'name', 'is_active']
        read_only_fields = ['id']


class VehicleModelSerializer(serializers.ModelSerializer):
    """Serializer pour les modèles de véhicules"""
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    
    class Meta:
        model = VehicleModel
        fields = ['id', 'name', 'brand', 'brand_name', 'is_active']
        read_only_fields = ['id', 'brand_name']


class VehicleColorSerializer(serializers.ModelSerializer):
    """Serializer pour les couleurs de véhicules"""
    
    class Meta:
        model = VehicleColor
        fields = ['id', 'name', 'is_active']
        read_only_fields = ['id']


class VehicleSerializer(serializers.ModelSerializer):
    """Serializer pour les véhicules"""
    driver_info = serializers.SerializerMethodField()
    etat_display = serializers.SerializerMethodField()
    images_urls = serializers.SerializerMethodField()
    
    # Informations des relations
    vehicle_type_name = serializers.CharField(source='vehicle_type.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    model_name = serializers.CharField(source='model.name', read_only=True)
    color_name = serializers.CharField(source='color.name', read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            'id', 'driver', 'driver_info',
            'vehicle_type', 'vehicle_type_name',
            'brand', 'brand_name',
            'model', 'model_name',
            'color', 'color_name',
            'nom', 'plaque_immatriculation', 'etat_vehicule', 'etat_display',
            'photo_exterieur_1', 'photo_exterieur_2',
            'photo_interieur_1', 'photo_interieur_2',
            'images_urls',
            'created_at', 'updated_at', 'is_active', 'is_online'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'driver_info',
            'etat_display', 'images_urls', 'vehicle_type_name',
            'brand_name', 'model_name', 'color_name'
        ]

    def get_driver_info(self, obj):
        return obj.get_driver_info()

    def get_etat_display(self, obj):
        return obj.get_etat_display_short()

    def get_images_urls(self, obj):
        request = self.context.get('request')
        return obj.get_images_urls(request)


class VehicleCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer un véhicule"""
    
    class Meta:
        model = Vehicle
        fields = [
            'driver', 'vehicle_type', 'brand', 'model', 'color',
            'nom', 'plaque_immatriculation', 'etat_vehicule',
            'photo_exterieur_1', 'photo_exterieur_2',
            'photo_interieur_1', 'photo_interieur_2'
        ]

    def validate_plaque_immatriculation(self, value):
        """Valide l'unicité de la plaque d'immatriculation"""
        if Vehicle.objects.filter(plaque_immatriculation=value).exists():
            raise serializers.ValidationError(
                "Cette plaque d'immatriculation est déjà utilisée."
            )
        return value


class VehicleUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour mettre à jour un véhicule"""
    
    class Meta:
        model = Vehicle
        fields = [
            'vehicle_type', 'brand', 'model', 'color',
            'nom', 'etat_vehicule',
            'photo_exterieur_1', 'photo_exterieur_2',
            'photo_interieur_1', 'photo_interieur_2',
            'is_active'
        ]

    def validate_plaque_immatriculation(self, value):
        """Valide l'unicité de la plaque d'immatriculation lors de la mise à jour"""
        if hasattr(self, 'instance') and self.instance:
            if Vehicle.objects.filter(
                plaque_immatriculation=value
            ).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(
                    "Cette plaque d'immatriculation est déjà utilisée."
                )
        return value


class VehicleListSerializer(serializers.ModelSerializer):
    """Serializer simple pour la liste des véhicules"""
    driver_name = serializers.SerializerMethodField()
    brand_model = serializers.SerializerMethodField()
    etat_display = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = [
            'id', 'driver', 'driver_name', 'brand_model',
            'nom', 'plaque_immatriculation', 'etat_display',
            'is_active', 'is_online', 'created_at'
        ]
        read_only_fields = ['id', 'driver_name', 'brand_model', 'etat_display']

    def get_driver_name(self, obj):
        return f"{obj.driver.name} {obj.driver.surname}"

    def get_brand_model(self, obj):
        return f"{obj.brand.name if obj.brand else 'N/A'} {obj.model.name if obj.model else 'N/A'}"

    def get_etat_display(self, obj):
        return obj.get_etat_display_short()