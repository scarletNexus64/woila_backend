from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
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

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_profile_picture_url(self, obj) -> str:
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
    confirm_password = serializers.CharField(min_length=6, write_only=True)
    name = serializers.CharField(max_length=100)
    surname = serializers.CharField(max_length=100)
    gender = serializers.ChoiceField(choices=UserDriver.GENDER_CHOICES)
    age = serializers.IntegerField(min_value=18, max_value=100)
    birthday = serializers.DateField()
    profile_picture = serializers.ImageField(required=False)
    referral_code = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate_phone_number(self, value):
        if UserDriver.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Ce numéro de téléphone est déjà utilisé par un chauffeur.")
        return value

    def validate(self, data):
        """Validate passwords match and age requirements"""
        # Check passwords match
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({
                'confirm_password': "Les mots de passe ne correspondent pas."
            })

        # Check minimum age (18 years)
        from datetime import date
        from dateutil.relativedelta import relativedelta

        birthday = data.get('birthday')
        if birthday:
            age_diff = relativedelta(date.today(), birthday)
            if age_diff.years < 18:
                raise serializers.ValidationError({
                    'birthday': "L'âge minimum requis est de 18 ans."
                })

        return data

    def create(self, validated_data):
        """Create new driver user"""
        from django.contrib.contenttypes.models import ContentType
        from applications.authentication.models import ReferralCode
        from applications.wallet.models import Wallet
        from core.models import GeneralConfig

        # Remove confirm_password before creating user
        validated_data.pop('confirm_password', None)
        referral_code = validated_data.pop('referral_code', None)

        # Create the driver
        driver = UserDriver.objects.create(**validated_data)

        # Create wallet with default balance
        driver_content_type = ContentType.objects.get_for_model(driver)
        Wallet.objects.create(
            user_type=driver_content_type,
            user_id=driver.id,
            balance=0
        )

        # Create referral code for this driver
        # Generate unique referral code
        import random
        import string
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        while ReferralCode.objects.filter(code=code).exists():
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

        ReferralCode.objects.create(
            code=code,
            user_type=driver_content_type,
            user_id=driver.id
        )

        # Process referral code if provided
        if referral_code and referral_code.strip():
            try:
                referrer_code = ReferralCode.objects.get(
                    code=referral_code,
                    is_active=True
                )

                # Get referral bonus from config (default 1000 FCFA)
                try:
                    config = GeneralConfig.objects.get(
                        search_key='referral_bonus',
                        active=True
                    )
                    referral_bonus = config.get_numeric_value() or 1000.0
                except GeneralConfig.DoesNotExist:
                    referral_bonus = 1000.0  # Valeur par défaut

                # Get referrer user via GenericForeignKey
                referrer_user = referrer_code.user_type.get_object_for_this_type(
                    id=referrer_code.user_id
                )

                # Add bonus to referrer's wallet
                referrer_wallet = Wallet.objects.get(
                    user_type=referrer_code.user_type,
                    user_id=referrer_code.user_id
                )
                referrer_wallet.add_credit(
                    referral_bonus,
                    f"Bonus de parrainage pour le code {referral_code}"
                )

                # Increment referral usage count
                referrer_code.used_count += 1
                referrer_code.save()

                # Send notification to referrer (async to not block registration)
                from applications.notifications.services.notification_service import NotificationService
                import threading

                def send_referral_notification():
                    NotificationService.send_referral_bonus_notification(
                        referrer_user=referrer_user,
                        referred_user=driver,
                        referral_code=referral_code,
                        bonus_amount=referral_bonus
                    )

                thread = threading.Thread(target=send_referral_notification)
                thread.start()

            except ReferralCode.DoesNotExist:
                # Invalid referral code, silently ignore
                pass
            except Exception as e:
                # Log error but don't fail registration
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error processing referral code: {str(e)}")

        return driver


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

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_profile_picture_url(self, obj) -> str:
        request = self.context.get('request')
        return obj.get_profile_picture_url(request)

    @extend_schema_field(serializers.IntegerField)
    def get_vehicles_count(self, obj) -> int:
        return obj.vehicles.count()

    @extend_schema_field(serializers.IntegerField)
    def get_documents_count(self, obj) -> int:
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

    @extend_schema_field(serializers.IntegerField)
    def get_documents_count(self, obj) -> int:
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

    def update(self, instance, validated_data):
        """Met à jour le profil du chauffeur"""
        # Mettre à jour les champs simples
        instance.name = validated_data.get('name', instance.name)
        instance.surname = validated_data.get('surname', instance.surname)
        instance.gender = validated_data.get('gender', instance.gender)
        instance.age = validated_data.get('age', instance.age)
        instance.birthday = validated_data.get('birthday', instance.birthday)

        # Gérer la photo de profil
        if 'profile_picture' in validated_data:
            # Supprimer l'ancienne photo si elle existe
            if instance.profile_picture:
                instance.profile_picture.delete(save=False)
            instance.profile_picture = validated_data['profile_picture']

        instance.save()
        return instance


class UserCustomerUpdateSerializer(serializers.Serializer):
    """Serializer pour la mise à jour des profils clients"""
    name = serializers.CharField(max_length=100, required=False)
    surname = serializers.CharField(max_length=100, required=False)
    profile_picture = serializers.ImageField(required=False)

    def update(self, instance, validated_data):
        """Met à jour le profil du client"""
        # Mettre à jour les champs simples
        instance.name = validated_data.get('name', instance.name)
        instance.surname = validated_data.get('surname', instance.surname)

        # Gérer la photo de profil
        if 'profile_picture' in validated_data:
            # Supprimer l'ancienne photo si elle existe
            if instance.profile_picture:
                instance.profile_picture.delete(save=False)
            instance.profile_picture = validated_data['profile_picture']

        instance.save()
        return instance