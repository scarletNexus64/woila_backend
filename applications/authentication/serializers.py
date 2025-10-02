from rest_framework import serializers
from .models import Token, OTPVerification, ReferralCode
from applications.users.models import UserDriver, UserCustomer


class LoginSerializer(serializers.Serializer):
    """Serializer pour la connexion"""
    phone_number = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True)
    user_type = serializers.ChoiceField(choices=[('driver', 'Driver'), ('customer', 'Customer')])

    def validate(self, data):
        from django.contrib.auth.hashers import check_password

        phone_number = data.get('phone_number')
        password = data.get('password')
        user_type = data.get('user_type')

        # Chercher l'utilisateur selon le type
        if user_type == 'driver':
            try:
                user = UserDriver.objects.get(phone_number=phone_number)
            except UserDriver.DoesNotExist:
                raise serializers.ValidationError("Numéro ou Mot de passe Incorrect")
        else:
            try:
                user = UserCustomer.objects.get(phone_number=phone_number)
            except UserCustomer.DoesNotExist:
                raise serializers.ValidationError("Numéro ou Mot de passe Incorrect")

        # Vérifier le mot de passe hashé
        if not check_password(password, user.password):
            raise serializers.ValidationError("Numéro ou Mot de passe Incorrect")

        # Ajouter l'utilisateur aux données validées
        data['user'] = user
        return data


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
    purpose = serializers.ChoiceField(
        choices=[('register', 'Register'), ('forgot_password', 'Forgot Password')],
        required=False,
        default='forgot_password'
    )


class VerifyOTPSerializer(serializers.Serializer):
    """Serializer pour vérifier un OTP"""
    phone_number = serializers.CharField(max_length=15)
    otp_code = serializers.CharField(max_length=4)  # 4 chiffres
    user_type = serializers.ChoiceField(choices=OTPVerification.USER_TYPE_CHOICES)
    purpose = serializers.ChoiceField(
        choices=[('register', 'Register'), ('forgot_password', 'Forgot Password')],
        required=False,
        default='register'
    )


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