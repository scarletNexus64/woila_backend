from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Vehicle, VehicleType, VehicleBrand, VehicleModel, VehicleColor
from typing import Dict


class VehicleSerializer(serializers.ModelSerializer):
    """Serializer pour les véhicules"""
    
    class Meta:
        model = Vehicle
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class VehicleCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour créer/modifier des véhicules"""
    # Accepter les IDs en plus des objets
    vehicle_type_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    brand_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    model_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    color_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Vehicle
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_approved']
        extra_kwargs = {
            'vehicle_type': {'required': False, 'allow_null': True},
            'brand': {'required': False, 'allow_null': True},
            'model': {'required': False, 'allow_null': True},
            'color': {'required': False, 'allow_null': True},
        }

    def create(self, validated_data):
        # Extraire les IDs si présents
        vehicle_type_id = validated_data.pop('vehicle_type_id', None)
        brand_id = validated_data.pop('brand_id', None)
        model_id = validated_data.pop('model_id', None)
        color_id = validated_data.pop('color_id', None)

        # Assigner les IDs aux champs ForeignKey
        if vehicle_type_id:
            validated_data['vehicle_type_id'] = vehicle_type_id
        if brand_id:
            validated_data['brand_id'] = brand_id
        if model_id:
            validated_data['model_id'] = model_id
        if color_id:
            validated_data['color_id'] = color_id

        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Extraire les IDs si présents
        vehicle_type_id = validated_data.pop('vehicle_type_id', None)
        brand_id = validated_data.pop('brand_id', None)
        model_id = validated_data.pop('model_id', None)
        color_id = validated_data.pop('color_id', None)

        # Assigner les IDs aux champs ForeignKey
        if vehicle_type_id:
            validated_data['vehicle_type_id'] = vehicle_type_id
        if brand_id:
            validated_data['brand_id'] = brand_id
        if model_id:
            validated_data['model_id'] = model_id
        if color_id:
            validated_data['color_id'] = color_id

        return super().update(instance, validated_data)


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
    brand = VehicleBrandSerializer(read_only=True)
    brand_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = VehicleModel
        fields = ['id', 'name', 'brand', 'brand_id', 'is_active']
        read_only_fields = ['id']


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

    @extend_schema_field(serializers.DictField)
    def get_driver_info(self, obj) -> Dict:
        return obj.get_driver_info()

    @extend_schema_field(serializers.CharField)
    def get_etat_display(self, obj) -> str:
        return obj.get_etat_display_short()

    @extend_schema_field(serializers.DictField)
    def get_images_urls(self, obj) -> Dict:
        request = self.context.get('request')
        return obj.get_images_urls(request)


class VehicleCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer un véhicule"""
    # Accepter les IDs en plus des objets
    vehicle_type_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    brand_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    model_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    color_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Vehicle
        fields = [
            'driver', 'vehicle_type', 'vehicle_type_id', 'brand', 'brand_id',
            'model', 'model_id', 'color', 'color_id',
            'nom', 'plaque_immatriculation', 'etat_vehicule',
            'photo_exterieur_1', 'photo_exterieur_2',
            'photo_interieur_1', 'photo_interieur_2'
        ]
        extra_kwargs = {
            'vehicle_type': {'required': False, 'allow_null': True},
            'brand': {'required': False, 'allow_null': True},
            'model': {'required': False, 'allow_null': True},
            'color': {'required': False, 'allow_null': True},
        }

    def create(self, validated_data):
        # Extraire les IDs si présents
        vehicle_type_id = validated_data.pop('vehicle_type_id', None)
        brand_id = validated_data.pop('brand_id', None)
        model_id = validated_data.pop('model_id', None)
        color_id = validated_data.pop('color_id', None)

        # Assigner les IDs aux champs ForeignKey
        if vehicle_type_id:
            validated_data['vehicle_type_id'] = vehicle_type_id
        if brand_id:
            validated_data['brand_id'] = brand_id
        if model_id:
            validated_data['model_id'] = model_id
        if color_id:
            validated_data['color_id'] = color_id

        return super().create(validated_data)

    def validate_plaque_immatriculation(self, value):
        """Valide l'unicité de la plaque d'immatriculation"""
        if Vehicle.objects.filter(plaque_immatriculation=value).exists():
            raise serializers.ValidationError(
                "Cette plaque d'immatriculation est déjà utilisée."
            )
        return value


class VehicleUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour mettre à jour un véhicule"""
    # Accepter les IDs en plus des objets
    vehicle_type_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    brand_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    model_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    color_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Vehicle
        fields = [
            'vehicle_type', 'vehicle_type_id', 'brand', 'brand_id',
            'model', 'model_id', 'color', 'color_id',
            'nom', 'etat_vehicule',
            'photo_exterieur_1', 'photo_exterieur_2',
            'photo_interieur_1', 'photo_interieur_2',
            'is_active'
        ]
        extra_kwargs = {
            'vehicle_type': {'required': False, 'allow_null': True},
            'brand': {'required': False, 'allow_null': True},
            'model': {'required': False, 'allow_null': True},
            'color': {'required': False, 'allow_null': True},
        }

    def update(self, instance, validated_data):
        # Extraire les IDs si présents
        vehicle_type_id = validated_data.pop('vehicle_type_id', None)
        brand_id = validated_data.pop('brand_id', None)
        model_id = validated_data.pop('model_id', None)
        color_id = validated_data.pop('color_id', None)

        # Assigner les IDs aux champs ForeignKey
        if vehicle_type_id:
            validated_data['vehicle_type_id'] = vehicle_type_id
        if brand_id:
            validated_data['brand_id'] = brand_id
        if model_id:
            validated_data['model_id'] = model_id
        if color_id:
            validated_data['color_id'] = color_id

        return super().update(instance, validated_data)

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

    @extend_schema_field(serializers.CharField)
    def get_driver_name(self, obj) -> str:
        return f"{obj.driver.name} {obj.driver.surname}"

    @extend_schema_field(serializers.CharField)
    def get_brand_model(self, obj) -> str:
        return f"{obj.brand.name if obj.brand else 'N/A'} {obj.model.name if obj.model else 'N/A'}"

    @extend_schema_field(serializers.CharField)
    def get_etat_display(self, obj) -> str:
        return obj.get_etat_display_short()