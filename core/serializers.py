from rest_framework import serializers
from .models import GeneralConfig, Country, City, VipZone, VipZoneKilometerRule


class GeneralConfigSerializer(serializers.ModelSerializer):
    """Serializer pour les configurations générales"""
    numeric_value = serializers.SerializerMethodField()
    boolean_value = serializers.SerializerMethodField()

    class Meta:
        model = GeneralConfig
        fields = [
            'id', 'nom', 'search_key', 'valeur', 'numeric_value',
            'boolean_value', 'active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'numeric_value', 'boolean_value']

    def get_numeric_value(self, obj):
        return obj.get_numeric_value()

    def get_boolean_value(self, obj):
        return obj.get_boolean_value()

    def validate_search_key(self, value):
        if hasattr(self, 'instance') and self.instance:
            if GeneralConfig.objects.filter(
                search_key=value
            ).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("Cette clé de recherche existe déjà.")
        else:
            if GeneralConfig.objects.filter(search_key=value).exists():
                raise serializers.ValidationError("Cette clé de recherche existe déjà.")
        return value


class CountrySerializer(serializers.ModelSerializer):
    """Serializer pour les pays"""
    cities_count = serializers.SerializerMethodField()

    class Meta:
        model = Country
        fields = ['id', 'name', 'active', 'cities_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'cities_count']

    def get_cities_count(self, obj):
        return obj.cities.filter(active=True).count()


class CitySerializer(serializers.ModelSerializer):
    """Serializer pour les villes"""
    country_name = serializers.CharField(source='country.name', read_only=True)
    vip_zones_count = serializers.SerializerMethodField()

    class Meta:
        model = City
        fields = [
            'id', 'country', 'country_name', 'name',
            'prix_jour', 'prix_nuit', 'vip_zones_count',
            'active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'country_name', 'vip_zones_count', 'created_at', 'updated_at']

    def get_vip_zones_count(self, obj):
        return obj.vip_zones.filter(active=True).count()


class VipZoneSerializer(serializers.ModelSerializer):
    """Serializer pour les zones VIP"""
    city_name = serializers.CharField(source='city.name', read_only=True)
    country_name = serializers.CharField(source='city.country.name', read_only=True)
    rules_count = serializers.SerializerMethodField()

    class Meta:
        model = VipZone
        fields = [
            'id', 'city', 'city_name', 'country_name', 'name',
            'additional_amount', 'rules_count', 'active',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'city_name', 'country_name', 'rules_count',
            'created_at', 'updated_at'
        ]

    def get_rules_count(self, obj):
        return obj.kilometer_rules.filter(active=True).count()


class VipZoneKilometerRuleSerializer(serializers.ModelSerializer):
    """Serializer pour les règles kilométriques des zones VIP"""
    vip_zone_name = serializers.CharField(source='vip_zone.name', read_only=True)

    class Meta:
        model = VipZoneKilometerRule
        fields = [
            'id', 'vip_zone', 'vip_zone_name',
            'min_km', 'max_km', 'additional_amount', 'active'
        ]
        read_only_fields = ['id', 'vip_zone_name']

    def validate(self, data):
        """Valide que min_km < max_km"""
        if data['min_km'] >= data['max_km']:
            raise serializers.ValidationError(
                "Le kilométrage minimum doit être inférieur au maximum."
            )
        return data