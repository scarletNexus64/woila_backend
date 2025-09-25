from rest_framework import serializers
from .models import UserDriver, UserCustomer, Document


class UserDriverSerializer(serializers.ModelSerializer):
    """Serializer de base pour UserDriver"""
    profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = UserDriver
        fields = [
            'id', 'phone_number', 'name', 'surname', 'gender', 'age',
            'birthday', 'profile_picture', 'profile_picture_url',
            'is_partenaire_interne', 'is_partenaire_externe',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {'password': {'write_only': True}}

    def get_profile_picture_url(self, obj):
        request = self.context.get('request')
        return obj.get_profile_picture_url(request)


class UserCustomerSerializer(serializers.ModelSerializer):
    """Serializer de base pour UserCustomer"""
    
    class Meta:
        model = UserCustomer
        fields = [
            'id', 'phone_number', 'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {'password': {'write_only': True}}


class RegisterDriverSerializer(serializers.Serializer):
    """Serializer pour l'inscription des chauffeurs"""
    phone_number = serializers.CharField(max_length=15)
    password = serializers.CharField(min_length=6, write_only=True)
    name = serializers.CharField(max_length=100)
    surname = serializers.CharField(max_length=100)
    gender = serializers.ChoiceField(choices=UserDriver.GENDER_CHOICES)
    age = serializers.IntegerField(min_value=18, max_value=100)
    birthday = serializers.DateField()
    profile_picture = serializers.ImageField(required=False)
    
    def validate_phone_number(self, value):
        if UserDriver.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Ce numéro de téléphone est déjà utilisé.")
        return value


class RegisterCustomerSerializer(serializers.Serializer):
    """Serializer pour l'inscription des clients"""
    phone_number = serializers.CharField(max_length=15)
    password = serializers.CharField(min_length=6, write_only=True)
    
    def validate_phone_number(self, value):
        if UserCustomer.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Ce numéro de téléphone est déjà utilisé.")
        return value


class UserDriverDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour UserDriver avec informations supplémentaires"""
    profile_picture_url = serializers.SerializerMethodField()
    vehicles_count = serializers.SerializerMethodField()
    documents_count = serializers.SerializerMethodField()

    class Meta:
        model = UserDriver
        fields = [
            'id', 'phone_number', 'name', 'surname', 'gender', 'age',
            'birthday', 'profile_picture', 'profile_picture_url',
            'is_partenaire_interne', 'is_partenaire_externe',
            'vehicles_count', 'documents_count',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'vehicles_count', 
            'documents_count', 'profile_picture_url'
        ]

    def get_profile_picture_url(self, obj):
        request = self.context.get('request')
        return obj.get_profile_picture_url(request)

    def get_vehicles_count(self, obj):
        return obj.vehicles.count()

    def get_documents_count(self, obj):
        return Document.objects.filter(user_id=obj.id, user_type='driver').count()


class UserCustomerDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour UserCustomer"""
    documents_count = serializers.SerializerMethodField()

    class Meta:
        model = UserCustomer
        fields = [
            'id', 'phone_number', 'documents_count',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'documents_count']

    def get_documents_count(self, obj):
        return Document.objects.filter(user_id=obj.id, user_type='customer').count()


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer pour les documents"""
    file_url = serializers.SerializerMethodField()
    file_size_display = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id', 'user_id', 'user_type', 'document_name', 'file',
            'file_url', 'original_filename', 'file_size', 'file_size_display',
            'content_type', 'uploaded_at', 'is_active'
        ]
        read_only_fields = [
            'id', 'original_filename', 'file_size', 'content_type',
            'uploaded_at', 'file_url', 'file_size_display'
        ]

    def get_file_url(self, obj):
        request = self.context.get('request')
        return obj.get_file_url(request)

    def get_file_size_display(self, obj):
        return obj.get_file_size_display()


class UserDriverUpdateSerializer(serializers.Serializer):
    """Serializer pour la mise à jour des profils chauffeurs"""
    name = serializers.CharField(max_length=100, required=False)
    surname = serializers.CharField(max_length=100, required=False)
    gender = serializers.ChoiceField(choices=UserDriver.GENDER_CHOICES, required=False)
    age = serializers.IntegerField(min_value=18, max_value=100, required=False)
    birthday = serializers.DateField(required=False)
    profile_picture = serializers.ImageField(required=False)


class UserCustomerUpdateSerializer(serializers.Serializer):
    """Serializer pour la mise à jour des profils clients"""
    # Pour l'instant, UserCustomer a peu de champs modifiables
    pass