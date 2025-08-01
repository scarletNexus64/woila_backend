from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from ..serializers import (
    UserDriverUpdateSerializer, UserCustomerUpdateSerializer,
    UserDriverDetailSerializer, UserCustomerDetailSerializer
)
from ..models import UserDriver, UserCustomer


@method_decorator(csrf_exempt, name='dispatch')
class DriverProfileView(APIView):
    """
    Vue pour gérer le profil d'un chauffeur (récupérer et modifier)
    """
    
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
        description='Modifie les informations personnelles d\'un chauffeur',
        request=UserDriverUpdateSerializer,
        responses={
            200: UserDriverDetailSerializer,
            400: {'description': 'Données invalides'},
            404: {'description': 'Chauffeur introuvable'},
        },
        examples=[
            OpenApiExample(
                'Update Driver Profile',
                summary='Modification profil chauffeur',
                description='Exemple de modification du profil chauffeur',
                value={
                    'name': 'Jean-Michel',
                    'surname': 'Dupont',
                    'gender': 'M',
                    'age': 36,
                    'birthday': '1988-05-15',
                    'phone_number': '+33123456789'
                },
                request_only=True,
            ),
            OpenApiExample(
                'Updated Profile',
                summary='Profil modifié',
                description='Réponse après modification réussie',
                value={
                    'success': True,
                    'message': 'Profil chauffeur modifié avec succès',
                    'driver': {
                        'id': 1,
                        'name': 'Jean-Michel',
                        'surname': 'Dupont',
                        'phone_number': '+33123456789',
                        'gender': 'M',
                        'age': 36,
                        'birthday': '1988-05-15',
                        'vehicles_count': 2,
                        'documents_count': 3,
                        'updated_at': '2023-12-05T16:00:00Z'
                    }
                },
                response_only=True,
            )
        ]
    )
    def put(self, request, driver_id):
        """
        Modifier le profil d'un chauffeur
        """
        driver = get_object_or_404(UserDriver, id=driver_id, is_active=True)
        
        serializer = UserDriverUpdateSerializer(
            instance=driver,
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            try:
                updated_driver = serializer.save()
                
                # Sérialiser la réponse
                response_serializer = UserDriverDetailSerializer(updated_driver, context={'request': request})
                
                return Response({
                    'success': True,
                    'message': 'Profil chauffeur modifié avec succès',
                    'driver': response_serializer.data
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


@method_decorator(csrf_exempt, name='dispatch')
class CustomerProfileView(APIView):
    """
    Vue pour gérer le profil d'un client (récupérer et modifier)
    """
    
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
        description='Modifie les informations personnelles d\'un client',
        request=UserCustomerUpdateSerializer,
        responses={
            200: UserCustomerDetailSerializer,
            400: {'description': 'Données invalides'},
            404: {'description': 'Client introuvable'},
        }
    )
    def put(self, request, customer_id):
        """
        Modifier le profil d'un client
        """
        customer = get_object_or_404(UserCustomer, id=customer_id, is_active=True)
        
        serializer = UserCustomerUpdateSerializer(
            instance=customer,
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            try:
                updated_customer = serializer.save()
                
                # Sérialiser la réponse
                response_serializer = UserCustomerDetailSerializer(updated_customer, context={'request': request})
                
                return Response({
                    'success': True,
                    'message': 'Profil client modifié avec succès',
                    'customer': response_serializer.data
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


@method_decorator(csrf_exempt, name='dispatch')
class AllDriversView(APIView):
    """
    Vue pour récupérer tous les chauffeurs
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
    Vue pour récupérer tous les clients
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
            from ..models import Document
            has_documents_bool = has_documents.lower() in ('true', '1', 'yes')
            if has_documents_bool:
                # Clients qui ont des documents
                customer_ids_with_docs = Document.objects.filter(
                    user_type='customer',
                    is_active=True
                ).values_list('user_id', flat=True).distinct()
                customers = customers.filter(id__in=customer_ids_with_docs)
            else:
                # Clients sans documents
                customer_ids_with_docs = Document.objects.filter(
                    user_type='customer',
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