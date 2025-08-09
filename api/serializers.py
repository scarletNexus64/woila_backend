from rest_framework import serializers
from .models import (
    UserDriver, UserCustomer, Token, Document, Vehicle, 
    GeneralConfig, Wallet, ReferralCode,
    VehicleType, VehicleBrand, VehicleModel, VehicleColor,
    OTPVerification, NotificationConfig
)
from django.contrib.auth.hashers import check_password
import uuid

# --- Referral System Serializers ---

class GeneralConfigSerializer(serializers.ModelSerializer):
    """
    Serializer pour les configurations générales
    """
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
        """Retourne la valeur numérique si possible"""
        return obj.get_numeric_value()
    
    def get_boolean_value(self, obj):
        """Retourne la valeur booléenne si possible"""
        return obj.get_boolean_value()
    
    def validate_search_key(self, value):
        """Valide l'unicité de la clé de recherche"""
        if hasattr(self, 'instance') and self.instance:
            if GeneralConfig.objects.filter(
                search_key=value
            ).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(
                    "Cette clé de recherche existe déjà."
                )
        else:
            if GeneralConfig.objects.filter(search_key=value).exists():
                raise serializers.ValidationError(
                    "Cette clé de recherche existe déjà."
                )
        return value


class GeneralConfigCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création de configurations générales avec exemples
    """
    class Meta:
        model = GeneralConfig
        fields = ['nom', 'search_key', 'valeur', 'active']
        extra_kwargs = {
            'nom': {
                'help_text': 'Nom descriptif (ex: "Réduction pendant les congés")'
            },
            'search_key': {
                'help_text': 'Clé unique (ex: "DISCOUNT_ORDER_FOR_HOLIDAYS")'
            },
            'valeur': {
                'help_text': 'Valeur de la configuration (ex: "20" pour 20%, "true/false" pour booléen)'
            },
            'active': {
                'help_text': 'Indique si cette configuration est active'
            }
        }
    
    def validate_search_key(self, value):
        """Valide l'unicité et le format de la clé de recherche"""
        import re
        
        # Vérifier le format (lettres majuscules et underscores)
        if not re.match(r'^[A-Z0-9_]+$', value):
            raise serializers.ValidationError(
                "La clé doit contenir uniquement des lettres majuscules, chiffres et underscores."
            )
        
        # Vérifier l'unicité
        if GeneralConfig.objects.filter(search_key=value).exists():
            raise serializers.ValidationError(
                "Cette clé de recherche existe déjà."
            )
        return value

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = '__all__'

class ReferralCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralCode
        fields = '__all__'


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
    profile_picture = serializers.ImageField(required=False, allow_null=True, help_text="Photo de profil (optionnel)")
    referral_code = serializers.CharField(max_length=8, required=False, allow_blank=True, help_text="Code de parrainage (optionnel)")
    
    def validate_phone_number(self, value):
        if UserDriver.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Ce numéro de téléphone est déjà utilisé par un chauffeur.")
        return value
    
    def validate_referral_code(self, value):
        """Valide le code de parrainage s'il est fourni"""
        if value:
            from .models import ReferralCode
            if not ReferralCode.objects.filter(code=value, is_active=True).exists():
                raise serializers.ValidationError("Ce code de parrainage n'existe pas ou n'est plus valide. Vérifiez le code ou contactez la personne qui vous l'a donné.")
        return value
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        return data
    
    def create(self, validated_data):
        from django.contrib.contenttypes.models import ContentType
        from .models import ReferralCode, Wallet, GeneralConfig
        
        # Extraire le code de parrainage et la photo avant la création
        referral_code = validated_data.pop('referral_code', None)
        validated_data.pop('confirm_password')
        profile_picture = validated_data.pop('profile_picture', None)
        
        # Créer le chauffeur
        user = UserDriver.objects.create(**validated_data)
        
        # Ajouter la photo de profil si fournie
        if profile_picture:
            user.profile_picture = profile_picture
            user.save()
        
        # Créer le wallet du chauffeur
        user_ct = ContentType.objects.get_for_model(UserDriver)
        wallet, created = Wallet.objects.get_or_create(
            user_type=user_ct,
            user_id=user.id,
            defaults={'balance': 0.00}
        )
        
        # Créer le code de parrainage pour ce chauffeur
        ReferralCode.objects.get_or_create(
            user_type=user_ct,
            user_id=user.id
        )
        
        # Traiter le bonus de parrainage si un code a été fourni
        if referral_code:
            try:
                # Trouver le parrain
                sponsor_referral = ReferralCode.objects.get(code=referral_code, is_active=True)
                
                # Récupérer le montant du bonus de parrainage depuis les configurations
                try:
                    bonus_config = GeneralConfig.objects.get(search_key='WELCOME_BONUS_AMOUNT', active=True)
                    bonus_amount = bonus_config.get_numeric_value()
                    
                    if bonus_amount and bonus_amount > 0:
                        # Créditer le wallet du PARRAIN (celui qui a le code de parrainage)
                        sponsor_wallet = Wallet.objects.get(
                            user_type=sponsor_referral.user_type,
                            user_id=sponsor_referral.user_id
                        )
                        from decimal import Decimal
                        sponsor_wallet.balance += Decimal(str(bonus_amount))
                        sponsor_wallet.save()
                        
                except GeneralConfig.DoesNotExist:
                    # Si la config n'existe pas, pas de bonus mais pas d'erreur non plus
                    pass
                    
            except ReferralCode.DoesNotExist:
                # Ne devrait pas arriver car on a validé avant, mais par sécurité
                pass
        
        return user


class RegisterCustomerSerializer(serializers.Serializer):
    """
    Serializer pour l'inscription des clients
    """
    phone_number = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)
    name = serializers.CharField(max_length=100)
    surname = serializers.CharField(max_length=100)
    profile_picture = serializers.ImageField(required=False, allow_null=True, help_text="Photo de profil (optionnel)")
    referral_code = serializers.CharField(max_length=8, required=False, allow_blank=True, help_text="Code de parrainage (optionnel)")
    
    def validate_phone_number(self, value):
        if UserCustomer.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Ce numéro de téléphone est déjà utilisé par un client.")
        return value
    
    def validate_referral_code(self, value):
        """Valide le code de parrainage s'il est fourni"""
        if value:
            from .models import ReferralCode
            if not ReferralCode.objects.filter(code=value, is_active=True).exists():
                raise serializers.ValidationError("Ce code de parrainage n'existe pas ou n'est plus valide. Vérifiez le code ou contactez la personne qui vous l'a donné.")
        return value
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        return data
    
    def create(self, validated_data):
        from django.contrib.contenttypes.models import ContentType
        from .models import ReferralCode, Wallet, GeneralConfig
        
        # Extraire le code de parrainage et la photo avant la création
        referral_code = validated_data.pop('referral_code', None)
        validated_data.pop('confirm_password')
        profile_picture = validated_data.pop('profile_picture', None)
        
        # Créer le client
        user = UserCustomer.objects.create(**validated_data)
        
        # Ajouter la photo de profil si fournie
        if profile_picture:
            user.profile_picture = profile_picture
            user.save()
        
        # Créer le wallet du client
        user_ct = ContentType.objects.get_for_model(UserCustomer)
        wallet, created = Wallet.objects.get_or_create(
            user_type=user_ct,
            user_id=user.id,
            defaults={'balance': 0.00}
        )
        
        # Créer le code de parrainage pour ce client
        ReferralCode.objects.get_or_create(
            user_type=user_ct,
            user_id=user.id
        )
        
        # Traiter le bonus de parrainage si un code a été fourni
        if referral_code:
            try:
                # Trouver le parrain
                sponsor_referral = ReferralCode.objects.get(code=referral_code, is_active=True)
                
                # Récupérer le montant du bonus de parrainage depuis les configurations
                try:
                    bonus_config = GeneralConfig.objects.get(search_key='WELCOME_BONUS_AMOUNT', active=True)
                    bonus_amount = bonus_config.get_numeric_value()
                    
                    if bonus_amount and bonus_amount > 0:
                        # Créditer le wallet du PARRAIN (celui qui a le code de parrainage)
                        sponsor_wallet = Wallet.objects.get(
                            user_type=sponsor_referral.user_type,
                            user_id=sponsor_referral.user_id
                        )
                        from decimal import Decimal
                        sponsor_wallet.balance += Decimal(str(bonus_amount))
                        sponsor_wallet.save()
                        
                except GeneralConfig.DoesNotExist:
                    # Si la config n'existe pas, pas de bonus mais pas d'erreur non plus
                    pass
                    
            except ReferralCode.DoesNotExist:
                # Ne devrait pas arriver car on a validé avant, mais par sécurité
                pass
        
        return user


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


class DocumentImportSerializer(serializers.Serializer):
    """
    Serializer pour l'importation de documents (flexible : 1 ou plusieurs fichiers)
    """
    user_id = serializers.IntegerField(min_value=1, help_text="ID de l'utilisateur")
    user_type = serializers.ChoiceField(
        choices=[('driver', 'Chauffeur'), ('customer', 'Client')],
        help_text="Type d'utilisateur (driver ou customer)"
    )
    document_name = serializers.CharField(
        max_length=100, 
        help_text="Nom/type du document (ex: 'Permis de conduire', 'CNI', 'Justificatif domicile')"
    )
    # Champ simple pour un seul fichier (compatible Swagger)
    file = serializers.FileField(
        allow_empty_file=False,
        help_text="Fichier image ou document",
        required=False
    )
    # Champ pour fichiers multiples (utilisation avancée)
    files = serializers.ListField(
        child=serializers.FileField(allow_empty_file=False),
        allow_empty=False,
        help_text="Plusieurs fichiers à importer",
        required=False
    )
    
    def validate_user_id(self, value):
        """Valide que l'utilisateur existe selon son type"""
        request = self.context.get('request')
        if request and hasattr(request, 'data'):
            user_type = request.data.get('user_type')
            if user_type == 'driver':
                if not UserDriver.objects.filter(id=value, is_active=True).exists():
                    raise serializers.ValidationError("Chauffeur introuvable ou inactif.")
            elif user_type == 'customer':
                if not UserCustomer.objects.filter(id=value, is_active=True).exists():
                    raise serializers.ValidationError("Client introuvable ou inactif.")
        return value
    
    def validate(self, data):
        """Valide les données et unifie les fichiers"""
        # Au moins un fichier doit être fourni
        file = data.get('file')
        files = data.get('files', [])
        
        if not file and not files:
            raise serializers.ValidationError({
                'files': 'Au moins un fichier doit être fourni (file ou files).'
            })
        
        # Unifier les fichiers dans une seule liste
        all_files = []
        if file:
            all_files.append(file)
        if files:
            all_files.extend(files)
        
        # Valider les fichiers
        self._validate_files(all_files)
        
        # Stocker tous les fichiers dans 'files' pour le traitement
        data['files'] = all_files
        
        return data
    
    def _validate_files(self, files):
        """Valide les fichiers (taille, type, etc.)"""
        max_file_size = 10 * 1024 * 1024  # 10 MB
        allowed_types = [
            'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf', 'application/msword', 
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]
        
        for file in files:
            if file.size > max_file_size:
                raise serializers.ValidationError(
                    f"Le fichier '{file.name}' est trop volumineux (max 10MB)."
                )
            
            if hasattr(file, 'content_type') and file.content_type not in allowed_types:
                raise serializers.ValidationError(
                    f"Type de fichier non autorisé pour '{file.name}'. "
                    f"Types acceptés : images (JPG, PNG, GIF, WebP), PDF, DOC, DOCX."
                )
    
    def create(self, validated_data):
        """Crée les documents en base"""
        files = validated_data.pop('files')
        documents = []
        
        for file in files:
            document = Document.objects.create(
                user_id=validated_data['user_id'],
                user_type=validated_data['user_type'],
                document_name=validated_data['document_name'],
                file=file
            )
            documents.append(document)
        
        return documents


class DocumentSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'affichage des documents
    """
    user_info = serializers.CharField(source='get_user_info', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'user_id', 'user_type', 'user_info', 'document_name', 
            'file_url', 'original_filename', 'file_size', 'content_type',
            'uploaded_at', 'is_active'
        ]
        read_only_fields = ['id', 'uploaded_at', 'user_info']
    
    def get_file_url(self, obj):
        """Retourne l'URL du fichier"""
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class VehicleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleType
        fields = '__all__'


class VehicleBrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleBrand
        fields = '__all__'


class VehicleModelSerializer(serializers.ModelSerializer):
    brand = VehicleBrandSerializer()

    class Meta:
        model = VehicleModel
        fields = '__all__'


class VehicleColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleColor
        fields = '__all__'


class VehicleSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'affichage des véhicules
    """
    driver_info = serializers.CharField(source='get_driver_info', read_only=True)
    etat_display = serializers.CharField(source='get_etat_display_short', read_only=True)
    images_urls = serializers.SerializerMethodField()
    vehicle_type = VehicleTypeSerializer()
    brand = VehicleBrandSerializer()
    model = VehicleModelSerializer()
    color = VehicleColorSerializer()

    class Meta:
        model = Vehicle
        fields = [
            'id', 'driver', 'driver_info', 'vehicle_type', 'brand', 'model', 'color', 'nom',
            'plaque_immatriculation', 'etat_vehicule', 'etat_display',
            'images_urls', 'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'driver_info', 'etat_display']
    
    def get_images_urls(self, obj):
        """Retourne les URLs des images"""
        request = self.context.get('request')
        return obj.get_images_urls(request)


class VehicleCreateUpdateSerializer(serializers.Serializer):
    """
    Serializer pour la création/modification de véhicules avec upload d'images
    """
    driver_id = serializers.IntegerField(min_value=1, help_text="ID du chauffeur")
    vehicle_type_id = serializers.IntegerField(min_value=1, help_text="ID du type de véhicule")
    brand_id = serializers.IntegerField(min_value=1, help_text="ID de la marque du véhicule")
    model_id = serializers.IntegerField(min_value=1, help_text="ID du modèle du véhicule")
    color_id = serializers.IntegerField(min_value=1, help_text="ID de la couleur du véhicule")
    nom = serializers.CharField(max_length=100, help_text="Nom du véhicule (ex: Camry, Série 3)")
    plaque_immatriculation = serializers.CharField(
        max_length=20, 
        help_text="Plaque d'immatriculation (unique)"
    )
    etat_vehicule = serializers.IntegerField(
        min_value=1, 
        max_value=10,
        help_text="État du véhicule sur une échelle de 1 à 10"
    )
    
    # Images du véhicule
    photo_exterieur_1 = serializers.ImageField(
        required=False,
        help_text="Photo extérieure 1"
    )
    photo_exterieur_2 = serializers.ImageField(
        required=False,
        help_text="Photo extérieure 2"
    )
    photo_interieur_1 = serializers.ImageField(
        required=False,
        help_text="Photo intérieure 1"
    )
    photo_interieur_2 = serializers.ImageField(
        required=False,
        help_text="Photo intérieure 2"
    )
    
    def validate_driver_id(self, value):
        """Valide que le chauffeur existe et est actif"""
        if not UserDriver.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Chauffeur introuvable ou inactif.")
        return value

    def validate_vehicle_type_id(self, value):
        if not VehicleType.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Type de véhicule introuvable ou inactif.")
        return value

    def validate_brand_id(self, value):
        if not VehicleBrand.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Marque de véhicule introuvable ou inactive.")
        return value

    def validate_model_id(self, value):
        if not VehicleModel.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Modèle de véhicule introuvable ou inactif.")
        return value

    def validate_color_id(self, value):
        if not VehicleColor.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Couleur de véhicule introuvable ou inactive.")
        return value
    
    def validate_plaque_immatriculation(self, value):
        """Valide l'unicité de la plaque d'immatriculation"""
        # Pour la modification, exclure le véhicule actuel
        if hasattr(self, 'instance') and self.instance:
            if Vehicle.objects.filter(
                plaque_immatriculation=value
            ).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(
                    "Cette plaque d'immatriculation est déjà utilisée."
                )
        else:
            # Pour la création
            if Vehicle.objects.filter(plaque_immatriculation=value).exists():
                raise serializers.ValidationError(
                    "Cette plaque d'immatriculation est déjà utilisée."
                )
        return value
    
    def validate(self, data):
        """Validations supplémentaires"""
        # Valider les images si fournies
        image_fields = ['photo_exterieur_1', 'photo_exterieur_2', 'photo_interieur_1', 'photo_interieur_2']
        max_size = 5 * 1024 * 1024  # 5 MB
        
        for field_name in image_fields:
            image = data.get(field_name)
            if image:
                if image.size > max_size:
                    raise serializers.ValidationError({
                        field_name: f"L'image est trop volumineuse (max 5MB). Taille: {image.size/1024/1024:.1f}MB"
                    })
                
                # Vérifier le type de fichier
                if not image.content_type.startswith('image/'):
                    raise serializers.ValidationError({
                        field_name: "Seules les images sont autorisées."
                    })
        
        return data
    
    def create(self, validated_data):
        """Créer un nouveau véhicule"""
        driver_id = validated_data.pop('driver_id')
        driver = UserDriver.objects.get(id=driver_id)
        
        vehicle = Vehicle.objects.create(
            driver=driver,
            **validated_data
        )
        return vehicle
    
    def update(self, instance, validated_data):
        """Mettre à jour un véhicule existant"""
        # Gérer le changement de chauffeur si nécessaire
        driver_id = validated_data.pop('driver_id', None)
        if driver_id:
            driver = UserDriver.objects.get(id=driver_id)
            instance.driver = driver
        
        # Mettre à jour les autres champs
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class UserDriverUpdateSerializer(serializers.Serializer):
    """
    Serializer pour la mise à jour du profil chauffeur
    """
    name = serializers.CharField(max_length=100, help_text="Prénom du chauffeur")
    surname = serializers.CharField(max_length=100, help_text="Nom de famille du chauffeur")
    gender = serializers.ChoiceField(
        choices=UserDriver.GENDER_CHOICES,
        help_text="Genre (M, F, O)"
    )
    age = serializers.IntegerField(min_value=18, max_value=80, help_text="Âge du chauffeur")
    birthday = serializers.DateField(help_text="Date de naissance")
    phone_number = serializers.CharField(max_length=15, help_text="Numéro de téléphone")
    profile_picture = serializers.ImageField(required=False, allow_null=True, help_text="Nouvelle photo de profil (optionnel)")
    
    def validate_phone_number(self, value):
        """Valide l'unicité du numéro de téléphone"""
        # Pour la modification, exclure le chauffeur actuel
        if hasattr(self, 'instance') and self.instance:
            if UserDriver.objects.filter(
                phone_number=value
            ).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(
                    "Ce numéro de téléphone est déjà utilisé par un autre chauffeur."
                )
        return value
    
    def update(self, instance, validated_data):
        """Mettre à jour le profil chauffeur"""
        profile_picture = validated_data.pop('profile_picture', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Gérer la photo de profil séparément
        if profile_picture is not None:
            instance.profile_picture = profile_picture
            
        instance.save()
        return instance


class UserCustomerUpdateSerializer(serializers.Serializer):
    """
    Serializer pour la mise à jour du profil client
    """
    name = serializers.CharField(max_length=100, help_text="Prénom du client")
    surname = serializers.CharField(max_length=100, help_text="Nom de famille du client")
    phone_number = serializers.CharField(max_length=15, help_text="Numéro de téléphone")
    profile_picture = serializers.ImageField(required=False, allow_null=True, help_text="Nouvelle photo de profil (optionnel)")
    
    def validate_phone_number(self, value):
        """Valide l'unicité du numéro de téléphone"""
        # Pour la modification, exclure le client actuel
        if hasattr(self, 'instance') and self.instance:
            if UserCustomer.objects.filter(
                phone_number=value
            ).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(
                    "Ce numéro de téléphone est déjà utilisé par un autre client."
                )
        return value
    
    def update(self, instance, validated_data):
        """Mettre à jour le profil client"""
        profile_picture = validated_data.pop('profile_picture', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Gérer la photo de profil séparément
        if profile_picture is not None:
            instance.profile_picture = profile_picture
            
        instance.save()
        return instance


class UserDriverDetailSerializer(serializers.ModelSerializer):
    """
    Serializer détaillé pour l'affichage du profil chauffeur
    """
    vehicles_count = serializers.SerializerMethodField()
    documents_count = serializers.SerializerMethodField()
    profile_picture_url = serializers.SerializerMethodField()
    
    class Meta:
        model = UserDriver
        fields = [
            'id', 'phone_number', 'name', 'surname', 'gender', 'age', 'birthday',
            'profile_picture_url', 'vehicles_count', 'documents_count', 'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'vehicles_count', 'documents_count', 'profile_picture_url']
    
    def get_vehicles_count(self, obj):
        """Nombre de véhicules actifs"""
        return obj.vehicles.filter(is_active=True).count()
    
    def get_documents_count(self, obj):
        """Nombre de documents actifs"""
        from .models import Document
        return Document.objects.filter(
            user_type='driver',
            user_id=obj.id,
            is_active=True
        ).count()
    
    def get_profile_picture_url(self, obj):
        """URL de la photo de profil"""
        request = self.context.get('request')
        return obj.get_profile_picture_url(request)


class UserCustomerDetailSerializer(serializers.ModelSerializer):
    """
    Serializer détaillé pour l'affichage du profil client
    """
    documents_count = serializers.SerializerMethodField()
    profile_picture_url = serializers.SerializerMethodField()
    
    class Meta:
        model = UserCustomer
        fields = [
            'id', 'phone_number', 'name', 'surname', 'profile_picture_url', 'documents_count',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'documents_count', 'profile_picture_url']
    
    def get_documents_count(self, obj):
        """Nombre de documents actifs"""
        from .models import Document
        return Document.objects.filter(
            user_type='customer',
            user_id=obj.id,
            is_active=True
        ).count()
    
    def get_profile_picture_url(self, obj):
        """URL de la photo de profil"""
        request = self.context.get('request')
        return obj.get_profile_picture_url(request)


# --- Serializers spécifiques au système de parrainage ---

class ReferralInfoSerializer(serializers.Serializer):
    """
    Serializer pour afficher les informations de parrainage d'un utilisateur
    """
    referral_code = serializers.CharField(read_only=True)
    wallet_balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    welcome_bonus_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    referral_system_active = serializers.BooleanField(read_only=True)
    user_info = serializers.CharField(read_only=True)


class ValidateReferralCodeSerializer(serializers.Serializer):
    """
    Serializer pour valider un code de parrainage
    """
    referral_code = serializers.CharField(max_length=8)
    
    def validate_referral_code(self, value):
        """Valide le code de parrainage"""
        if not ReferralCode.objects.filter(code=value, is_active=True).exists():
            raise serializers.ValidationError(
                "Ce code de parrainage n'existe pas ou n'est plus valide. "
                "Vérifiez le code ou contactez la personne qui vous l'a donné."
            )
        return value
    
    def to_representation(self, instance):
        """Retourne les informations du parrain"""
        referral_code = self.validated_data['referral_code']
        
        try:
            referral = ReferralCode.objects.get(code=referral_code, is_active=True)
            
            # Récupérer le bonus de bienvenue
            try:
                bonus_config = GeneralConfig.objects.get(search_key='WELCOME_BONUS_AMOUNT', active=True)
                bonus_amount = bonus_config.get_numeric_value() or 0
            except GeneralConfig.DoesNotExist:
                bonus_amount = 0
            
            return {
                'valid': True,
                'referral_code': referral_code,
                'sponsor_info': str(referral.user),
                'welcome_bonus_amount': bonus_amount,
                'message': f"✅ Code valide! Vous recevrez {bonus_amount} FCFA en bonus de bienvenue."
            }
            
        except ReferralCode.DoesNotExist:
            return {
                'valid': False,
                'message': "Ce code de parrainage n'existe pas."
            }


class WalletBalanceSerializer(serializers.ModelSerializer):
    """
    Serializer pour afficher le solde du wallet
    """
    user_info = serializers.CharField(source='user', read_only=True)
    balance_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Wallet
        fields = ['balance', 'balance_formatted', 'user_info', 'created_at', 'updated_at']
        read_only_fields = ['balance', 'created_at', 'updated_at']
    
    def get_balance_formatted(self, obj):
        """Retourne le solde formaté"""
        return f"{obj.balance:,.0f} FCFA".replace(',', ' ')


class ReferralStatsSerializer(serializers.Serializer):
    """
    Serializer pour les statistiques de parrainage
    """
    total_referrals = serializers.IntegerField(read_only=True)
    active_referrals = serializers.IntegerField(read_only=True)
    total_bonus_distributed = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    welcome_bonus_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)


# --- OTP System Serializers ---

class OTPGenerateSerializer(serializers.Serializer):
    """
    Serializer pour la génération d'OTP
    """
    identifier = serializers.CharField(
        max_length=100,
        help_text="Numéro de téléphone ou email pour recevoir l'OTP"
    )
    
    def validate_identifier(self, value):
        """Valide l'identifiant (numéro de téléphone ou email)"""
        # Vérifier si c'est un numéro de téléphone ou un email
        import re
        
        # Pattern pour numéro de téléphone international
        phone_pattern = r'^\+?[1-9]\d{1,14}$'
        # Pattern pour email basique
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not (re.match(phone_pattern, value) or re.match(email_pattern, value)):
            raise serializers.ValidationError(
                "L'identifiant doit être un numéro de téléphone valide (+237xxxxxxxx) ou un email valide."
            )
        
        return value


class OTPVerifySerializer(serializers.Serializer):
    """
    Serializer pour la vérification d'OTP
    """
    identifier = serializers.CharField(
        max_length=100,
        help_text="Numéro de téléphone ou email utilisé pour recevoir l'OTP"
    )
    otp = serializers.CharField(
        max_length=4,
        min_length=4,
        help_text="Code OTP à 4 chiffres"
    )
    
    def validate_otp(self, value):
        """Valide que l'OTP contient uniquement des chiffres"""
        if not value.isdigit():
            raise serializers.ValidationError("L'OTP doit contenir uniquement des chiffres.")
        return value


class OTPVerificationSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'affichage des vérifications OTP
    """
    is_valid_status = serializers.SerializerMethodField()
    
    class Meta:
        model = OTPVerification
        fields = ['id', 'identifier', 'otp', 'created_at', 'is_verified', 'is_valid_status']
        read_only_fields = ['id', 'otp', 'created_at', 'is_verified', 'is_valid_status']
    
    def get_is_valid_status(self, obj):
        """Retourne si l'OTP est encore valide"""
        return obj.is_valid()


class NotificationConfigSerializer(serializers.ModelSerializer):
    """
    Serializer pour la configuration des notifications
    """
    class Meta:
        model = NotificationConfig
        fields = [
            'id', 'default_channel',
            'nexah_base_url', 'nexah_send_endpoint', 'nexah_credits_endpoint',
            'nexah_user', 'nexah_password', 'nexah_sender_id',
            'whatsapp_api_token', 'whatsapp_api_version', 'whatsapp_phone_number_id',
            'whatsapp_template_name', 'whatsapp_language',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'nexah_password': {'write_only': True},
            'whatsapp_api_token': {'write_only': True},
        }


class NotificationConfigPublicSerializer(serializers.ModelSerializer):
    """
    Serializer public pour la configuration des notifications (sans les secrets)
    """
    class Meta:
        model = NotificationConfig
        fields = [
            'default_channel', 'nexah_sender_id', 'whatsapp_template_name', 
            'whatsapp_language', 'updated_at'
        ]
        read_only_fields = ['default_channel', 'nexah_sender_id', 'whatsapp_template_name', 
                          'whatsapp_language', 'updated_at']


# --- Forgot Password Serializer ---

class ForgotPasswordSerializer(serializers.Serializer):
    """
    Serializer pour la réinitialisation du mot de passe
    """
    phone_number = serializers.CharField(max_length=15, help_text="Numéro de téléphone de l'utilisateur")
    user_type = serializers.ChoiceField(
        choices=[('driver', 'Driver'), ('customer', 'Customer')],
        help_text="Type d'utilisateur (driver ou customer)"
    )
    new_password = serializers.CharField(
        write_only=True,
        min_length=6,
        help_text="Nouveau mot de passe (minimum 6 caractères)"
    )
    confirm_password = serializers.CharField(
        write_only=True,
        help_text="Confirmation du nouveau mot de passe"
    )
    
    def validate(self, data):
        """Valide les données et trouve l'utilisateur"""
        phone_number = data.get('phone_number')
        user_type = data.get('user_type')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        # Vérifier que les mots de passe correspondent
        if new_password != confirm_password:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        
        # Trouver l'utilisateur
        if user_type == 'driver':
            try:
                user = UserDriver.objects.get(phone_number=phone_number)
            except UserDriver.DoesNotExist:
                raise serializers.ValidationError("Aucun chauffeur trouvé avec ce numéro de téléphone.")
        else:
            try:
                user = UserCustomer.objects.get(phone_number=phone_number)
            except UserCustomer.DoesNotExist:
                raise serializers.ValidationError("Aucun client trouvé avec ce numéro de téléphone.")
        
        data['user'] = user
        return data