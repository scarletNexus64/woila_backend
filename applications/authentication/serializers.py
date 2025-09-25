from rest_framework import serializers
from .models import Token, OTPVerification, ReferralCode
from applications.users.models import UserDriver, UserCustomer


class LoginSerializer(serializers.Serializer):
    """Serializer pour la connexion"""
    phone_number = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True)


class LogoutSerializer(serializers.Serializer):
    """Serializer pour la déconnexion"""
    pass  # Utilise le token dans les headers


class TokenSerializer(serializers.ModelSerializer):
    """Serializer pour les tokens"""
    
    class Meta:
        model = Token
        fields = ['id', 'token', 'user_type', 'user_id', 'created_at', 'is_active']
        read_only_fields = ['id', 'token', 'created_at']


class OTPVerificationSerializer(serializers.ModelSerializer):
    """Serializer pour la vérification OTP"""
    
    class Meta:
        model = OTPVerification
        fields = [
            'id', 'phone_number', 'otp_code', 'user_type',
            'created_at', 'expires_at', 'is_verified', 'attempts'
        ]
        read_only_fields = ['id', 'created_at', 'expires_at', 'is_verified', 'attempts']
        extra_kwargs = {'otp_code': {'write_only': True}}


class GenerateOTPSerializer(serializers.Serializer):
    """Serializer pour générer un OTP"""
    phone_number = serializers.CharField(max_length=15)
    user_type = serializers.ChoiceField(choices=OTPVerification.USER_TYPE_CHOICES)


class VerifyOTPSerializer(serializers.Serializer):
    """Serializer pour vérifier un OTP"""
    phone_number = serializers.CharField(max_length=15)
    otp_code = serializers.CharField(max_length=6)
    user_type = serializers.ChoiceField(choices=OTPVerification.USER_TYPE_CHOICES)


class ReferralCodeSerializer(serializers.ModelSerializer):
    """Serializer pour les codes de parrainage"""
    
    class Meta:
        model = ReferralCode
        fields = ['id', 'code', 'driver_id', 'created_at', 'is_active', 'used_count']
        read_only_fields = ['id', 'code', 'created_at', 'used_count']


class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer pour la réinitialisation de mot de passe"""
    phone_number = serializers.CharField(max_length=15)
    user_type = serializers.ChoiceField(choices=[('driver', 'Driver'), ('customer', 'Customer')])


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer pour définir un nouveau mot de passe"""
    phone_number = serializers.CharField(max_length=15)
    otp_code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=6, write_only=True)
    user_type = serializers.ChoiceField(choices=[('driver', 'Driver'), ('customer', 'Customer')])