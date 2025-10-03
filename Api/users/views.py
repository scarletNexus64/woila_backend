# EXISTING ENDPOINTS - DO NOT MODIFY URLs - Already integrated in production
# User views migrated from api.viewsets.profiles

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated

# Import from api app (legacy)
from users.models import UserDriver, UserCustomer
from authentication.models import Token
from .serializers import (
    UserDriverUpdateSerializer, UserCustomerUpdateSerializer,
    UserDriverDetailSerializer, UserCustomerDetailSerializer
)


@method_decorator(csrf_exempt, name='dispatch')
class MeProfileView(APIView):
    """
    EXISTING ENDPOINT: GET /api/auth/me/
    DO NOT MODIFY - Already integrated in production
    """
    
    @extend_schema(
        tags=['Profils'],
        summary='Récupérer le profil de l\'utilisateur connecté',
        description='Récupère les informations détaillées de l\'utilisateur connecté via son token',
        responses={
            200: {
                'description': 'Profil utilisateur récupéré avec succès',
                'examples': {
                    'application/json': {
                        'success': True,
                        'user_type': 'customer',  # ou 'driver'
                        'user': {
                            'id': 1,
                            'name': 'John',
                            'surname': 'Doe', 
                            'phone_number': '+237123456789',
                            'is_active': True,
                            'created_at': '2023-12-01T10:30:00Z',
                            'updated_at': '2023-12-05T15:45:00Z'
                        }
                    }
                }
            },
            401: {'description': 'Token manquant ou invalide'},
            404: {'description': 'Utilisateur introuvable'},
        }
    )
    def get(self, request):
        """
        Récupérer le profil de l'utilisateur connecté via le token
        """
        # Récupérer le token depuis l'en-tête Authorization
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({
                'success': False,
                'message': 'Token manquant ou format invalide'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        token_key = auth_header.split(' ')[1]
        
        try:
            # Chercher le token dans la base de données
            token = Token.objects.get(token=token_key, is_active=True)
        except Token.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Token invalide ou expiré'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Récupérer l'utilisateur via la relation GenericForeignKey
        user = token.user

        # Vérifier que l'utilisateur existe et est actif
        if not user or not user.is_active:
            return Response({
                'success': False,
                'message': 'Utilisateur associé au token introuvable ou inactif'
            }, status=status.HTTP_404_NOT_FOUND)

        # Sérialiser selon le type d'utilisateur
        if isinstance(user, UserDriver):
            serializer = UserDriverDetailSerializer(user, context={'request': request})
        elif isinstance(user, UserCustomer):
            serializer = UserCustomerDetailSerializer(user, context={'request': request})
        else:
            return Response({
                'success': False,
                'message': 'Type d\'utilisateur invalide'
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'success': True,
            'user_type': 'driver' if isinstance(user, UserDriver) else 'customer',
            'user': serializer.data
        }, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class DriverProfileView(APIView):
    """
    EXISTING ENDPOINT: GET /api/profiles/driver/{driver_id}/
    DO NOT MODIFY - Already integrated in production
    """
    parser_classes = [MultiPartParser, FormParser]
    
    @extend_schema(
        tags=['Profils'],
        summary='Récupérer le profil chauffeur',
        description='Récupère les informations détaillées d\'un chauffeur par son ID',
        responses={
            200: UserDriverDetailSerializer,
            404: {'description': 'Chauffeur introuvable'},
        },
        examples=[
            OpenApiExample(
                'Driver Profile',
                summary='Profil chauffeur',
                description='Informations détaillées du profil chauffeur',
                value={
                    'success': True,
                    'driver': {
                        'id': 1,
                        'phone_number': '+33123456789',
                        'name': 'Jean',
                        'surname': 'Dupont',
                        'gender': 'M',
                        'age': 35,
                        'birthday': '1988-05-15',
                        'vehicles_count': 2,
                        'documents_count': 3,
                        'created_at': '2023-12-01T10:30:00Z',
                        'updated_at': '2023-12-05T15:45:00Z',
                        'is_active': True
                    }
                },
                response_only=True,
            )
        ]
    )
    def get(self, request, driver_id):
        """
        Récupérer le profil d'un chauffeur
        """
        driver = get_object_or_404(UserDriver, id=driver_id, is_active=True)
        serializer = UserDriverDetailSerializer(driver, context={'request': request})
        
        return Response({
            'success': True,
            'driver': serializer.data
        }, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Profils'],
        summary='Modifier le profil chauffeur',
        description='Modifie les informations personnelles d\'un chauffeur. Utilisez un formulaire multipart pour uploader une nouvelle photo de profil.',
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string', 'example': 'Jean-Michel'},
                    'surname': {'type': 'string', 'example': 'Dupont'},
                    'gender': {'type': 'string', 'enum': ['M', 'F', 'O'], 'example': 'M'},
                    'age': {'type': 'integer', 'example': 36},
                    'birthday': {'type': 'string', 'format': 'date', 'example': '1988-05-15'},
                    'phone_number': {'type': 'string', 'example': '+237123456789'},
                    'profile_picture': {'type': 'string', 'format': 'binary', 'description': 'Nouvelle photo de profil (optionnel)'}
                },
                'required': ['name', 'surname', 'gender', 'age', 'birthday', 'phone_number']
            }
        },
        responses={
            200: {
                'description': 'Profil modifié avec succès',
                'examples': {
                    'application/json': {
                        'success': True,
                        'message': 'Profil chauffeur modifié avec succès',
                        'driver': {
                            'id': 1,
                            'name': 'Jean-Michel',
                            'surname': 'Dupont',
                            'phone_number': '+237123456789',
                            'gender': 'M',
                            'age': 36,
                            'birthday': '1988-05-15',
                            'profile_picture_url': 'http://localhost:8000/media/profile_pictures/driver/1/new_photo.jpg',
                            'vehicles_count': 2,
                            'documents_count': 3,
                            'updated_at': '2023-12-05T16:00:00Z'
                        }
                    }
                }
            },
            400: {'description': 'Données invalides'},
            404: {'description': 'Chauffeur introuvable'},
        }
    )
    def put(self, request, driver_id):
        """
        Modifier le profil d'un chauffeur
        """
        print(f"🔄 PUT /api/users/driver/{driver_id}/ - Updating driver profile")
        print(f"📝 Request data: {request.data}")
        print(f"📸 Request files: {request.FILES}")

        driver = get_object_or_404(UserDriver, id=driver_id, is_active=True)
        print(f"✅ Driver found: {driver.name} {driver.surname}")

        serializer = UserDriverUpdateSerializer(
            instance=driver,
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            try:
                print(f"✅ Serializer valid, saving...")
                updated_driver = serializer.save()
                print(f"✅ Driver updated successfully")

                # Sérialiser la réponse
                response_serializer = UserDriverDetailSerializer(updated_driver, context={'request': request})

                return Response({
                    'success': True,
                    'message': 'Profil chauffeur modifié avec succès',
                    'driver': response_serializer.data
                }, status=status.HTTP_200_OK)

            except Exception as e:
                print(f"❌ Error saving driver: {str(e)}")
                import traceback
                traceback.print_exc()
                return Response({
                    'success': False,
                    'message': f'Erreur lors de la modification : {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        print(f"❌ Serializer validation failed: {serializer.errors}")
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class CustomerProfileView(APIView):
    """
    EXISTING ENDPOINT: GET /api/profiles/customer/{customer_id}/
    DO NOT MODIFY - Already integrated in production
    """
    parser_classes = [MultiPartParser, FormParser]
    
    @extend_schema(
        tags=['Profils'],
        summary='Récupérer le profil client',
        description='Récupère les informations détaillées d\'un client par son ID',
        responses={
            200: UserCustomerDetailSerializer,
            404: {'description': 'Client introuvable'},
        }
    )
    def get(self, request, customer_id):
        """
        Récupérer le profil d'un client
        """
        customer = get_object_or_404(UserCustomer, id=customer_id, is_active=True)
        serializer = UserCustomerDetailSerializer(customer, context={'request': request})
        
        return Response({
            'success': True,
            'customer': serializer.data
        }, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Profils'],
        summary='Modifier le profil client',
        description='Modifie les informations personnelles d\'un client. Utilisez un formulaire multipart pour uploader une nouvelle photo de profil.',
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string', 'example': 'Marie'},
                    'surname': {'type': 'string', 'example': 'Martin'},
                    'phone_number': {'type': 'string', 'example': '+237987654321'},
                    'profile_picture': {'type': 'string', 'format': 'binary', 'description': 'Nouvelle photo de profil (optionnel)'}
                },
                'required': ['name', 'surname', 'phone_number']
            }
        },
        responses={
            200: {
                'description': 'Profil modifié avec succès',
                'examples': {
                    'application/json': {
                        'success': True,
                        'message': 'Profil client modifié avec succès',
                        'customer': {
                            'id': 1,
                            'name': 'Marie',
                            'surname': 'Martin',
                            'phone_number': '+237987654321',
                            'profile_picture_url': 'http://localhost:8000/media/profile_pictures/customer/1/new_photo.jpg',
                            'documents_count': 2,
                            'updated_at': '2023-12-05T16:00:00Z'
                        }
                    }
                }
            },
            400: {'description': 'Données invalides'},
            404: {'description': 'Client introuvable'},
        }
    )
    def put(self, request, customer_id):
        """
        Modifier le profil d'un client
        """
        print(f"🔄 PUT /api/users/customer/{customer_id}/ - Updating customer profile")
        print(f"📝 Request data: {request.data}")
        print(f"📸 Request files: {request.FILES}")

        customer = get_object_or_404(UserCustomer, id=customer_id, is_active=True)
        print(f"✅ Customer found: {customer.name} {customer.surname}")

        serializer = UserCustomerUpdateSerializer(
            instance=customer,
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            try:
                print(f"✅ Serializer valid, saving...")
                updated_customer = serializer.save()
                print(f"✅ Customer updated successfully")

                # Sérialiser la réponse
                response_serializer = UserCustomerDetailSerializer(updated_customer, context={'request': request})

                return Response({
                    'success': True,
                    'message': 'Profil client modifié avec succès',
                    'customer': response_serializer.data
                }, status=status.HTTP_200_OK)

            except Exception as e:
                print(f"❌ Error saving customer: {str(e)}")
                import traceback
                traceback.print_exc()
                return Response({
                    'success': False,
                    'message': f'Erreur lors de la modification : {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        print(f"❌ Serializer validation failed: {serializer.errors}")
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class AllDriversView(APIView):
    """
    EXISTING ENDPOINT: GET /api/profiles/drivers/
    DO NOT MODIFY - Already integrated in production
    """
    
    @extend_schema(
        tags=['Profils'],
        summary='Lister tous les chauffeurs',
        description='Récupère la liste de tous les chauffeurs actifs avec leurs informations détaillées',
        parameters=[
            OpenApiParameter(
                name='is_active',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filtrer par chauffeurs actifs/inactifs (par défaut: actifs uniquement)',
                required=False
            ),
            OpenApiParameter(
                name='gender',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filtrer par genre (M, F, O)',
                required=False
            ),
            OpenApiParameter(
                name='has_vehicles',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filtrer les chauffeurs qui ont des véhicules',
                required=False
            )
        ],
        responses={
            200: UserDriverDetailSerializer(many=True),
        }
    )
    def get(self, request):
        """
        Récupérer tous les chauffeurs avec filtres optionnels
        """
        # Base queryset
        drivers = UserDriver.objects.all()
        
        # Filtres
        is_active = request.query_params.get('is_active')
        gender = request.query_params.get('gender')
        has_vehicles = request.query_params.get('has_vehicles')
        
        # Filtrer par statut actif
        if is_active is not None:
            is_active_bool = is_active.lower() in ('true', '1', 'yes')
            drivers = drivers.filter(is_active=is_active_bool)
        else:
            # Par défaut, ne montrer que les chauffeurs actifs
            drivers = drivers.filter(is_active=True)
        
        # Filtrer par genre
        if gender and gender.upper() in ['M', 'F', 'O']:
            drivers = drivers.filter(gender=gender.upper())
        
        # Filtrer par possession de véhicules
        if has_vehicles is not None:
            has_vehicles_bool = has_vehicles.lower() in ('true', '1', 'yes')
            if has_vehicles_bool:
                drivers = drivers.filter(vehicles__is_active=True).distinct()
            else:
                # Chauffeurs sans véhicules
                drivers = drivers.filter(vehicles__isnull=True)
        
        # Ordonner par date de création (plus récents en premier)
        drivers = drivers.order_by('-created_at')
        
        serializer = UserDriverDetailSerializer(drivers, many=True, context={'request': request})
        
        return Response({
            'success': True,
            'count': len(serializer.data),
            'drivers': serializer.data
        }, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class AllCustomersView(APIView):
    """
    EXISTING ENDPOINT: GET /api/profiles/customers/
    DO NOT MODIFY - Already integrated in production
    """
    
    @extend_schema(
        tags=['Profils'],
        summary='Lister tous les clients',
        description='Récupère la liste de tous les clients actifs avec leurs informations détaillées',
        parameters=[
            OpenApiParameter(
                name='is_active',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filtrer par clients actifs/inactifs (par défaut: actifs uniquement)',
                required=False
            ),
            OpenApiParameter(
                name='has_documents',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filtrer les clients qui ont des documents',
                required=False
            )
        ],
        responses={
            200: UserCustomerDetailSerializer(many=True),
        }
    )
    def get(self, request):
        """
        Récupérer tous les clients avec filtres optionnels
        """
        # Base queryset
        customers = UserCustomer.objects.all()
        
        # Filtres
        is_active = request.query_params.get('is_active')
        has_documents = request.query_params.get('has_documents')
        
        # Filtrer par statut actif
        if is_active is not None:
            is_active_bool = is_active.lower() in ('true', '1', 'yes')
            customers = customers.filter(is_active=is_active_bool)
        else:
            # Par défaut, ne montrer que les clients actifs
            customers = customers.filter(is_active=True)
        
        # Filtrer par possession de documents
        if has_documents is not None:
            from users.models import Document
            from django.contrib.contenttypes.models import ContentType
            customer_content_type = ContentType.objects.get_for_model(UserCustomer)
            has_documents_bool = has_documents.lower() in ('true', '1', 'yes')
            if has_documents_bool:
                # Clients qui ont des documents
                customer_ids_with_docs = Document.objects.filter(
                    user_type=customer_content_type,
                    is_active=True
                ).values_list('user_id', flat=True).distinct()
                customers = customers.filter(id__in=customer_ids_with_docs)
            else:
                # Clients sans documents
                customer_ids_with_docs = Document.objects.filter(
                    user_type=customer_content_type,
                    is_active=True
                ).values_list('user_id', flat=True).distinct()
                customers = customers.exclude(id__in=customer_ids_with_docs)
        
        # Ordonner par date de création (plus récents en premier)
        customers = customers.order_by('-created_at')
        
        serializer = UserCustomerDetailSerializer(customers, many=True, context={'request': request})
        
        return Response({
            'success': True,
            'count': len(serializer.data),
            'customers': serializer.data
        }, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class DocumentUploadView(APIView):
    """
    Endpoint pour uploader les documents des utilisateurs (drivers et customers)
    POST /api/documents/upload/
    """
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        tags=['Documents'],
        summary='Uploader un document utilisateur',
        description='Upload un document pour un utilisateur (driver ou customer) avec support multi-fichiers',
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'integer', 'example': 1},
                    'user_type': {'type': 'string', 'enum': ['driver', 'customer'], 'example': 'driver'},
                    'document_name': {'type': 'string', 'example': 'Carte d\'identité nationale'},
                    'file': {'type': 'string', 'format': 'binary', 'description': 'Fichier principal'},
                    'file_2': {'type': 'string', 'format': 'binary', 'description': 'Fichier additionnel (optionnel)'},
                },
                'required': ['user_id', 'user_type', 'document_name', 'file']
            }
        },
        responses={
            201: {
                'description': 'Document(s) uploadé(s) avec succès',
                'examples': {
                    'application/json': {
                        'success': True,
                        'message': '2 document(s) uploadé(s) avec succès',
                        'documents': [
                            {
                                'id': 1,
                                'document_name': 'Carte d\'identité nationale',
                                'file_url': 'http://localhost:8000/media/documents/driver/1/id_card.jpg',
                                'file_size': 125000,
                                'uploaded_at': '2023-12-05T16:00:00Z'
                            }
                        ]
                    }
                }
            },
            400: {'description': 'Données invalides ou fichier manquant'},
            404: {'description': 'Utilisateur introuvable'},
        }
    )
    def post(self, request):
        """
        Upload un ou plusieurs documents pour un utilisateur
        """
        from .models import Document
        from .serializers import DocumentSerializer

        user_id = request.data.get('user_id')
        user_type = request.data.get('user_type')
        document_name = request.data.get('document_name')

        # Validation des champs requis
        if not user_id or not user_type or not document_name:
            return Response({
                'success': False,
                'message': 'user_id, user_type et document_name sont requis'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Vérifier que l'utilisateur existe
        if user_type == 'driver':
            if not UserDriver.objects.filter(id=user_id, is_active=True).exists():
                return Response({
                    'success': False,
                    'message': 'Chauffeur introuvable'
                }, status=status.HTTP_404_NOT_FOUND)
        elif user_type == 'customer':
            if not UserCustomer.objects.filter(id=user_id, is_active=True).exists():
                return Response({
                    'success': False,
                    'message': 'Client introuvable'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({
                'success': False,
                'message': 'user_type doit être "driver" ou "customer"'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Collecter tous les fichiers (file, file_2, file_3, etc.)
        files = []
        for key in request.FILES:
            if key.startswith('file'):
                files.append(request.FILES[key])

        if not files:
            return Response({
                'success': False,
                'message': 'Aucun fichier fourni'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Créer les documents
        created_documents = []
        try:
            for file in files:
                document = Document.objects.create(
                    user_id=user_id,
                    user_type=user_type,
                    document_name=document_name,
                    file=file
                )
                created_documents.append(document)

            # Sérialiser les documents créés
            serializer = DocumentSerializer(created_documents, many=True, context={'request': request})

            return Response({
                'success': True,
                'message': f'{len(created_documents)} document(s) uploadé(s) avec succès',
                'documents': serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            # En cas d'erreur, supprimer les documents déjà créés
            for doc in created_documents:
                try:
                    doc.file.delete()
                    doc.delete()
                except:
                    pass

            return Response({
                'success': False,
                'message': f'Erreur lors de l\'upload : {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)