from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from ..serializers import VehicleCreateUpdateSerializer, VehicleSerializer
from ..models import Vehicle, UserDriver


@method_decorator(csrf_exempt, name='dispatch')
class VehicleCreateView(APIView):
    """
    Vue pour créer un véhicule avec upload d'images
    """
    parser_classes = [MultiPartParser, FormParser]
    
    @extend_schema(
        tags=['Véhicules'],
        summary='Créer un véhicule',
        description='Permet à un chauffeur de créer un véhicule avec ses informations et photos. '
                   'Supporte l\'upload de 4 images : 2 extérieures et 2 intérieures.',
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'driver_id': {
                        'type': 'integer',
                        'description': 'ID du chauffeur',
                        'example': 1
                    },
                    'marque': {
                        'type': 'string',
                        'description': 'Marque du véhicule',
                        'example': 'Toyota'
                    },
                    'nom': {
                        'type': 'string',
                        'description': 'Nom du véhicule',
                        'example': 'Camry'
                    },
                    'modele': {
                        'type': 'string',
                        'description': 'Modèle',
                        'example': '2020'
                    },
                    'couleur': {
                        'type': 'string',
                        'description': 'Couleur',
                        'example': 'Noir'
                    },
                    'plaque_immatriculation': {
                        'type': 'string',
                        'description': 'Plaque d\'immatriculation',
                        'example': 'AB-123-CD'
                    },
                    'etat_vehicule': {
                        'type': 'integer',
                        'minimum': 1,
                        'maximum': 10,
                        'description': 'État du véhicule (1-10)',
                        'example': 8
                    },
                    'photo_exterieur_1': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'Photo extérieure 1'
                    },
                    'photo_exterieur_2': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'Photo extérieure 2'
                    },
                    'photo_interieur_1': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'Photo intérieure 1'
                    },
                    'photo_interieur_2': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'Photo intérieure 2'
                    }
                },
                'required': ['driver_id', 'marque', 'nom', 'modele', 'couleur', 'plaque_immatriculation', 'etat_vehicule']
            }
        },
        responses={
            201: VehicleSerializer,
            400: {'description': 'Données invalides'},
            404: {'description': 'Chauffeur introuvable'},
        },
        examples=[
            OpenApiExample(
                'Successful Creation',
                summary='Véhicule créé avec succès',
                description='Réponse après création réussie d\'un véhicule',
                value={
                    'success': True,
                    'message': 'Véhicule créé avec succès',
                    'vehicle': {
                        'id': 1,
                        'driver': 1,
                        'driver_info': 'Jean Dupont (+33123456789)',
                        'marque': 'Toyota',
                        'nom': 'Camry',
                        'modele': '2020',
                        'couleur': 'Noir',
                        'plaque_immatriculation': 'AB-123-CD',
                        'etat_vehicule': 8,
                        'etat_display': '8/10',
                        'images_urls': {
                            'photo_exterieur_1': 'http://localhost:8000/media/vehicles/1/1/ext1.jpg',
                            'photo_exterieur_2': 'http://localhost:8000/media/vehicles/1/1/ext2.jpg',
                            'photo_interieur_1': None,
                            'photo_interieur_2': None
                        },
                        'created_at': '2023-12-01T10:30:00Z',
                        'is_active': True
                    }
                },
                response_only=True,
            )
        ]
    )
    def post(self, request):
        """
        Créer un nouveau véhicule
        """
        # Préparer les données avec les fichiers
        data = request.data.copy()
        for key, file in request.FILES.items():
            data[key] = file
        
        serializer = VehicleCreateUpdateSerializer(data=data, context={'request': request})
        
        if serializer.is_valid():
            try:
                vehicle = serializer.save()
                
                # Sérialiser la réponse
                vehicle_serializer = VehicleSerializer(vehicle, context={'request': request})
                
                return Response({
                    'success': True,
                    'message': 'Véhicule créé avec succès',
                    'vehicle': vehicle_serializer.data
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response({
                    'success': False,
                    'message': f'Erreur lors de la création : {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class VehicleListView(APIView):
    """
    Vue pour lister tous les véhicules ou ceux d'un chauffeur spécifique
    """
    
    @extend_schema(
        tags=['Véhicules'],
        summary='Lister les véhicules',
        description='Récupère la liste de tous les véhicules ou ceux d\'un chauffeur spécifique',
        parameters=[
            OpenApiParameter(
                name='driver_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID du chauffeur (optionnel - filtre par chauffeur)',
                required=False
            ),
            OpenApiParameter(
                name='is_active',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filtrer par véhicules actifs/inactifs',
                required=False
            )
        ],
        responses={
            200: VehicleSerializer(many=True),
        }
    )
    def get(self, request):
        """
        Lister les véhicules
        """
        driver_id = request.query_params.get('driver_id')
        is_active = request.query_params.get('is_active')
        
        # Base queryset
        vehicles = Vehicle.objects.select_related('driver')
        
        # Filtrer par chauffeur si spécifié
        if driver_id:
            vehicles = vehicles.filter(driver_id=driver_id, driver__is_active=True)
        
        # Filtrer par statut actif si spécifié
        if is_active is not None:
            is_active_bool = is_active.lower() in ('true', '1', 'yes')
            vehicles = vehicles.filter(is_active=is_active_bool)
        
        serializer = VehicleSerializer(vehicles, many=True, context={'request': request})
        
        return Response({
            'success': True,
            'count': len(serializer.data),
            'vehicles': serializer.data
        }, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class VehicleDetailView(APIView):
    """
    Vue pour récupérer, modifier ou supprimer un véhicule spécifique
    """
    parser_classes = [MultiPartParser, FormParser]
    
    @extend_schema(
        tags=['Véhicules'],
        summary='Récupérer un véhicule',
        description='Récupère les détails d\'un véhicule par son ID',
        responses={
            200: VehicleSerializer,
            404: {'description': 'Véhicule introuvable'},
        }
    )
    def get(self, request, vehicle_id):
        """
        Récupérer un véhicule par son ID
        """
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        serializer = VehicleSerializer(vehicle, context={'request': request})
        
        return Response({
            'success': True,
            'vehicle': serializer.data
        }, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Véhicules'],
        summary='Modifier un véhicule',
        description='Modifie les informations et/ou les photos d\'un véhicule existant',
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'driver_id': {'type': 'integer'},
                    'marque': {'type': 'string'},
                    'nom': {'type': 'string'},
                    'modele': {'type': 'string'},
                    'couleur': {'type': 'string'},
                    'plaque_immatriculation': {'type': 'string'},
                    'etat_vehicule': {'type': 'integer', 'minimum': 1, 'maximum': 10},
                    'photo_exterieur_1': {'type': 'string', 'format': 'binary'},
                    'photo_exterieur_2': {'type': 'string', 'format': 'binary'},
                    'photo_interieur_1': {'type': 'string', 'format': 'binary'},
                    'photo_interieur_2': {'type': 'string', 'format': 'binary'}
                }
            }
        },
        responses={
            200: VehicleSerializer,
            400: {'description': 'Données invalides'},
            404: {'description': 'Véhicule introuvable'},
        }
    )
    def put(self, request, vehicle_id):
        """
        Modifier un véhicule
        """
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        
        # Préparer les données avec les fichiers
        data = request.data.copy()
        for key, file in request.FILES.items():
            data[key] = file
        
        serializer = VehicleCreateUpdateSerializer(
            instance=vehicle,
            data=data,
            context={'request': request},
            partial=True
        )
        
        if serializer.is_valid():
            try:
                updated_vehicle = serializer.save()
                
                # Sérialiser la réponse
                vehicle_serializer = VehicleSerializer(updated_vehicle, context={'request': request})
                
                return Response({
                    'success': True,
                    'message': 'Véhicule modifié avec succès',
                    'vehicle': vehicle_serializer.data
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                return Response({
                    'success': False,
                    'message': f'Erreur lors de la modification : {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        tags=['Véhicules'],
        summary='Supprimer un véhicule',
        description='Supprime définitivement un véhicule (ou le désactive selon la logique métier)',
        responses={
            200: {'description': 'Véhicule supprimé avec succès'},
            404: {'description': 'Véhicule introuvable'},
        }
    )
    def delete(self, request, vehicle_id):
        """
        Supprimer un véhicule (soft delete - désactiver)
        """
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        
        # Soft delete - désactiver plutôt que supprimer
        vehicle.is_active = False
        vehicle.save()
        
        return Response({
            'success': True,
            'message': f'Véhicule {vehicle.marque} {vehicle.nom} ({vehicle.plaque_immatriculation}) désactivé avec succès'
        }, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class VehiclesByDriverView(APIView):
    """
    Vue spécialisée pour récupérer tous les véhicules d'un chauffeur
    """
    
    @extend_schema(
        tags=['Véhicules'],
        summary='Véhicules par chauffeur',
        description='Récupère tous les véhicules d\'un chauffeur spécifique par son ID',
        responses={
            200: VehicleSerializer(many=True),
            404: {'description': 'Chauffeur introuvable'},
        }
    )
    def get(self, request, driver_id):
        """
        Récupérer tous les véhicules d'un chauffeur
        """
        # Vérifier que le chauffeur existe
        driver = get_object_or_404(UserDriver, id=driver_id, is_active=True)
        
        # Récupérer ses véhicules
        vehicles = Vehicle.objects.filter(driver=driver, is_active=True)
        
        serializer = VehicleSerializer(vehicles, many=True, context={'request': request})
        
        return Response({
            'success': True,
            'driver_info': f"{driver.name} {driver.surname} ({driver.phone_number})",
            'count': len(serializer.data),
            'vehicles': serializer.data
        }, status=status.HTTP_200_OK)