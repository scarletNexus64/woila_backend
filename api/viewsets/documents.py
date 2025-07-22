from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema, OpenApiExample
from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from ..serializers import DocumentImportSerializer, DocumentSerializer
from ..models import Document, UserDriver, UserCustomer


@method_decorator(csrf_exempt, name='dispatch')
class DocumentImportView(APIView):
    """
    Vue pour l'importation de documents (images, PDF, etc.)
    Supporte l'upload de fichiers multiples via formulaire
    """
    parser_classes = [MultiPartParser, FormParser]
    
    @extend_schema(
        tags=['Documents'],
        summary='Importer des documents',
        description='Permet d\'importer un ou plusieurs documents (images, PDF) pour un utilisateur. '
                   'Supporte les formats : JPG, PNG, GIF, WebP, PDF, DOC, DOCX. Taille max : 10MB par fichier.',
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'user_id': {
                        'type': 'integer',
                        'description': 'ID de l\'utilisateur',
                        'example': 1
                    },
                    'user_type': {
                        'type': 'string',
                        'enum': ['driver', 'customer'],
                        'description': 'Type d\'utilisateur',
                        'example': 'driver'
                    },
                    'document_name': {
                        'type': 'string',
                        'description': 'Nom/type du document',
                        'example': 'Permis de conduire'
                    },
                    'file': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'Fichier à importer (pour un seul fichier)'
                    },
                    'files': {
                        'type': 'array',
                        'items': {
                            'type': 'string',
                            'format': 'binary'
                        },
                        'description': 'Plusieurs fichiers à importer (optionnel)'
                    }
                },
                'required': ['user_id', 'user_type', 'document_name']
            }
        },
        responses={
            201: {'description': 'Documents importés avec succès'},
            400: {'description': 'Données invalides ou fichiers non conformes'},
            404: {'description': 'Utilisateur introuvable'},
        },
        examples=[
            OpenApiExample(
                'Successful Import',
                summary='Import réussi',
                description='Réponse après import réussi de documents',
                value={
                    'success': True,
                    'message': '2 document(s) importé(s) avec succès pour Jean Dupont (Chauffeur)',
                    'documents': [
                        {
                            'id': 1,
                            'user_id': 1,
                            'user_type': 'driver',
                            'user_info': 'Jean Dupont (+33123456789)',
                            'document_name': 'Permis de conduire',
                            'file_url': 'http://localhost:8000/media/documents/driver/1/Permis_de_conduire/permis.jpg',
                            'original_filename': 'permis.jpg',
                            'file_size': 1048576,
                            'content_type': 'image/jpeg',
                            'uploaded_at': '2023-12-01T10:30:00Z',
                            'is_active': True
                        }
                    ]
                },
                response_only=True,
            ),
            OpenApiExample(
                'Validation Error',
                summary='Erreur de validation',
                description='Erreur lors de la validation des données',
                value={
                    'success': False,
                    'errors': {
                        'user_id': ['Chauffeur introuvable ou inactif.'],
                        'files': ['Le fichier est trop volumineux (max 10MB).']
                    }
                },
                response_only=True,
            )
        ]
    )
    def post(self, request):
        """
        Importer des documents pour un utilisateur
        """
        # Préparer les données pour le serializer
        data = request.data.copy()
        
        # Ajouter les fichiers de request.FILES
        for key, file in request.FILES.items():
            data[key] = file
        
        # Validation avec le serializer
        serializer = DocumentImportSerializer(data=data, context={'request': request})
        
        if serializer.is_valid():
            try:
                # Créer les documents
                documents = serializer.save()
                
                # Sérialiser la réponse
                document_serializer = DocumentSerializer(
                    documents, 
                    many=True, 
                    context={'request': request}
                )
                
                # Récupérer les infos utilisateur pour le message
                user_type = serializer.validated_data['user_type']
                user_id = serializer.validated_data['user_id']
                
                if user_type == 'driver':
                    user = UserDriver.objects.get(id=user_id)
                    user_info = f"{user.name} {user.surname} (Chauffeur)"
                else:
                    user = UserCustomer.objects.get(id=user_id)
                    user_info = f"{user.name} {user.surname} (Client)"
                
                return Response({
                    'success': True,
                    'message': f'{len(documents)} document(s) importé(s) avec succès pour {user_info}',
                    'documents': document_serializer.data
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response({
                    'success': False,
                    'message': f'Erreur lors de l\'importation : {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class DocumentListView(APIView):
    """
    Vue pour lister les documents d'un utilisateur
    """
    
    @extend_schema(
        tags=['Documents'],
        summary='Lister les documents',
        description='Récupère la liste des documents d\'un utilisateur spécifique',
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID de l\'utilisateur',
                required=True
            ),
            OpenApiParameter(
                name='user_type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Type d\'utilisateur (driver ou customer)',
                required=True,
                enum=['driver', 'customer']
            ),
            OpenApiParameter(
                name='document_name',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filtrer par nom de document',
                required=False
            )
        ],
        responses={
            200: DocumentSerializer(many=True),
            400: {'description': 'Paramètres manquants'},
            404: {'description': 'Utilisateur introuvable'},
        }
    )
    def get(self, request):
        """
        Récupérer les documents d'un utilisateur
        """
        user_id = request.query_params.get('user_id')
        user_type = request.query_params.get('user_type')
        document_name = request.query_params.get('document_name')
        
        if not user_id or not user_type:
            return Response({
                'success': False,
                'message': 'Paramètres user_id et user_type requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier que l'utilisateur existe
        if user_type == 'driver':
            if not UserDriver.objects.filter(id=user_id, is_active=True).exists():
                return Response({
                    'success': False,
                    'message': 'Chauffeur introuvable ou inactif'
                }, status=status.HTTP_404_NOT_FOUND)
        elif user_type == 'customer':
            if not UserCustomer.objects.filter(id=user_id, is_active=True).exists():
                return Response({
                    'success': False,
                    'message': 'Client introuvable ou inactif'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({
                'success': False,
                'message': 'Type d\'utilisateur invalide (driver ou customer)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Récupérer les documents
        documents = Document.objects.filter(
            user_id=user_id,
            user_type=user_type,
            is_active=True
        )
        
        # Filtrer par nom de document si spécifié
        if document_name:
            documents = documents.filter(document_name__icontains=document_name)
        
        serializer = DocumentSerializer(documents, many=True, context={'request': request})
        
        return Response({
            'success': True,
            'count': len(serializer.data),
            'documents': serializer.data
        }, status=status.HTTP_200_OK)