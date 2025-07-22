from rest_framework import serializers
from .models import UserDriver, UserCustomer, Token, Document, Vehicle
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


class VehicleSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'affichage des véhicules
    """
    driver_info = serializers.CharField(source='get_driver_info', read_only=True)
    etat_display = serializers.CharField(source='get_etat_display_short', read_only=True)
    images_urls = serializers.SerializerMethodField()
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'driver', 'driver_info', 'marque', 'nom', 'modele', 'couleur',
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
    marque = serializers.CharField(max_length=50, help_text="Marque du véhicule (ex: Toyota, BMW)")
    nom = serializers.CharField(max_length=100, help_text="Nom du véhicule (ex: Camry, Série 3)")
    modele = serializers.CharField(max_length=50, help_text="Modèle (ex: 2020, Sport)")
    couleur = serializers.CharField(max_length=30, help_text="Couleur du véhicule")
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