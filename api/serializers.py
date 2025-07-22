from rest_framework import serializers
from .models import UserDriver, UserCustomer, Token
from django.contrib.auth.hashers import check_password
import uuid

class UserDriverSerializer(serializers.ModelSerializer):
    """
    Serializer pour les chauffeurs
    """
    confirm_password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = UserDriver
        fields = ['id', 'phone_number', 'password', 'confirm_password', 'name', 
                 'surname', 'gender', 'age', 'birthday', 'created_at', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True},
            'id': {'read_only': True},
            'created_at': {'read_only': True},
        }
    
    def validate(self, data):
        if 'password' in data and 'confirm_password' in data:
            if data['password'] != data['confirm_password']:
                raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        return data
    
    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        return UserDriver.objects.create(**validated_data)


class UserCustomerSerializer(serializers.ModelSerializer):
    """
    Serializer pour les clients
    """
    confirm_password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = UserCustomer
        fields = ['id', 'phone_number', 'password', 'confirm_password', 'name', 
                 'surname', 'created_at', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True},
            'id': {'read_only': True},
            'created_at': {'read_only': True},
        }
    
    def validate(self, data):
        if 'password' in data and 'confirm_password' in data:
            if data['password'] != data['confirm_password']:
                raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        return data
    
    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        return UserCustomer.objects.create(**validated_data)


class TokenSerializer(serializers.ModelSerializer):
    """
    Serializer pour les tokens d'authentification
    """
    class Meta:
        model = Token
        fields = ['token', 'user_type', 'user_id', 'created_at', 'is_active']
        extra_kwargs = {
            'token': {'read_only': True},
            'created_at': {'read_only': True},
        }


class LoginSerializer(serializers.Serializer):
    """
    Serializer pour la connexion (login)
    """
    phone_number = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True)
    user_type = serializers.ChoiceField(choices=[('driver', 'Driver'), ('customer', 'Customer')])
    
    def validate(self, data):
        phone_number = data.get('phone_number')
        password = data.get('password')
        user_type = data.get('user_type')
        
        if user_type == 'driver':
            try:
                user = UserDriver.objects.get(phone_number=phone_number, is_active=True)
            except UserDriver.DoesNotExist:
                raise serializers.ValidationError("Chauffeur introuvable ou inactif.")
        else:
            try:
                user = UserCustomer.objects.get(phone_number=phone_number, is_active=True)
            except UserCustomer.DoesNotExist:
                raise serializers.ValidationError("Client introuvable ou inactif.")
        
        if not user.check_password(password):
            raise serializers.ValidationError("Mot de passe incorrect.")
        
        data['user'] = user
        return data


class RegisterDriverSerializer(serializers.Serializer):
    """
    Serializer pour l'inscription des chauffeurs
    """
    phone_number = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)
    name = serializers.CharField(max_length=100)
    surname = serializers.CharField(max_length=100)
    gender = serializers.ChoiceField(choices=UserDriver.GENDER_CHOICES)
    age = serializers.IntegerField(min_value=18, max_value=80)
    birthday = serializers.DateField()
    
    def validate_phone_number(self, value):
        if UserDriver.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Ce numéro de téléphone est déjà utilisé par un chauffeur.")
        return value
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        return data
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        return UserDriver.objects.create(**validated_data)


class RegisterCustomerSerializer(serializers.Serializer):
    """
    Serializer pour l'inscription des clients
    """
    phone_number = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)
    name = serializers.CharField(max_length=100)
    surname = serializers.CharField(max_length=100)
    
    def validate_phone_number(self, value):
        if UserCustomer.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Ce numéro de téléphone est déjà utilisé par un client.")
        return value
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        return data
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        return UserCustomer.objects.create(**validated_data)


class LogoutSerializer(serializers.Serializer):
    """
    Serializer pour la déconnexion (logout)
    """
    token = serializers.UUIDField()
    
    def validate_token(self, value):
        try:
            token = Token.objects.get(token=value, is_active=True)
        except Token.DoesNotExist:
            raise serializers.ValidationError("Token invalide ou expiré.")
        return value