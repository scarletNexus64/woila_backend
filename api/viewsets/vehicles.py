from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from ..serializers import (
    VehicleCreateUpdateSerializer, VehicleSerializer,
    VehicleTypeSerializer, VehicleBrandSerializer, VehicleModelSerializer, VehicleColorSerializer
)
from ..models import (
    Vehicle, UserDriver, VehicleType, VehicleBrand, VehicleModel, VehicleColor
)


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
        request=VehicleCreateUpdateSerializer,
        responses={
            201: VehicleSerializer,
            400: {'description': 'Données invalides'},
            404: {'description': 'Chauffeur, type, marque, modèle ou couleur introuvable'},
        }
    )
    def post(self, request):
        """
        Créer un nouveau véhicule
        """
        data = request.data.copy()
        for key, file in request.FILES.items():
            data[key] = file
        
        serializer = VehicleCreateUpdateSerializer(data=data, context={'request': request})
        
        if serializer.is_valid():
            try:
                vehicle = serializer.save()
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
        
        vehicles = Vehicle.objects.select_related('driver', 'vehicle_type', 'brand', 'model', 'color')
        
        if driver_id:
            vehicles = vehicles.filter(driver_id=driver_id, driver__is_active=True)
        
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
    
    def get_object(self, vehicle_id):
        return get_object_or_404(
            Vehicle.objects.select_related('driver', 'vehicle_type', 'brand', 'model', 'color'), 
            id=vehicle_id
        )

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
        vehicle = self.get_object(vehicle_id)
        serializer = VehicleSerializer(vehicle, context={'request': request})
        
        return Response({
            'success': True,
            'vehicle': serializer.data
        }, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Véhicules'],
        summary='Modifier un véhicule',
        description='Modifie les informations et/ou les photos d\'un véhicule existant',
        request=VehicleCreateUpdateSerializer,
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
        vehicle = self.get_object(vehicle_id)
        
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
        vehicle = self.get_object(vehicle_id)
        
        vehicle.is_active = False
        vehicle.save()
        
        return Response({
            'success': True,
            'message': f'Véhicule {vehicle.brand} {vehicle.model} ({vehicle.plaque_immatriculation}) désactivé avec succès'
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
        driver = get_object_or_404(UserDriver, id=driver_id, is_active=True)
        
        vehicles = Vehicle.objects.filter(driver=driver, is_active=True).select_related(
            'vehicle_type', 'brand', 'model', 'color'
        )
        
        serializer = VehicleSerializer(vehicles, many=True, context={'request': request})
        
        return Response({
            'success': True,
            'driver_info': f"{driver.name} {driver.surname} ({driver.phone_number})",
            'count': len(serializer.data),
            'vehicles': serializer.data
        }, status=status.HTTP_200_OK)


# --- Vues pour les nouvelles entités --- #

class VehicleTypeListView(APIView):
    @extend_schema(tags=['Véhicules Config'], summary='Lister les types de véhicule')
    def get(self, request):
        types = VehicleType.objects.filter(is_active=True)
        serializer = VehicleTypeSerializer(types, many=True)
        return Response({'success': True, 'types': serializer.data}, status=status.HTTP_200_OK)


class VehicleBrandListView(APIView):
    @extend_schema(tags=['Véhicules Config'], summary='Lister les marques de véhicule')
    def get(self, request):
        brands = VehicleBrand.objects.filter(is_active=True)
        serializer = VehicleBrandSerializer(brands, many=True)
        return Response({'success': True, 'brands': serializer.data}, status=status.HTTP_200_OK)


class VehicleModelListView(APIView):
    @extend_schema(tags=['Véhicules Config'], summary='Lister les modèles de véhicule')
    def get(self, request):
        models = VehicleModel.objects.filter(is_active=True).select_related('brand')
        serializer = VehicleModelSerializer(models, many=True)
        return Response({'success': True, 'models': serializer.data}, status=status.HTTP_200_OK)


class VehicleColorListView(APIView):
    @extend_schema(tags=['Véhicules Config'], summary='Lister les couleurs de véhicule')
    def get(self, request):
        colors = VehicleColor.objects.filter(is_active=True)
        serializer = VehicleColorSerializer(colors, many=True)
        return Response({'success': True, 'colors': serializer.data}, status=status.HTTP_200_OK)
