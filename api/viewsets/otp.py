# api/viewsets/otp.py

from random import randint
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from ..serializers import OTPGenerateSerializer, OTPVerifySerializer
from ..models import OTPVerification, UserDriver, UserCustomer
from ..services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class GenerateOTPView(APIView):
    """
    Vue pour générer un code OTP
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Génère un code OTP à 4 chiffres et l'envoie par SMS/WhatsApp au numéro fourni. Exemple: {\"identifier\": \"+237123456789\"}",
        request_body=OTPGenerateSerializer,
        responses={
            200: openapi.Response(
                description="OTP généré et envoyé avec succès",
                examples={
                    "application/json": {
                        "message": "Un code de vérification a été envoyé à votre numéro de téléphone.",
                        "sms_sent": True,
                        "identifier": "+237123456789"
                    }
                }
            ),
            400: openapi.Response(
                description="Erreur dans la requête ou numéro déjà utilisé",
                examples={
                    "application/json": {
                        "error": "Ce numéro est déjà utilisé"
                    }
                }
            )
        },
        tags=['OTP']
    )
    def post(self, request):
        serializer = OTPGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        identifier = serializer.validated_data['identifier']
        
        # Vérifier si le numéro de téléphone est déjà utilisé (seulement pour les numéros de téléphone)
        if '+' in identifier or identifier.startswith('237'):  # C'est probablement un numéro de téléphone
            if (UserDriver.objects.filter(phone_number=identifier).exists() or 
                UserCustomer.objects.filter(phone_number=identifier).exists()):
                return Response(
                    {'error': 'Ce numéro est déjà utilisé'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Générer un code OTP à 4 chiffres
        otp = str(randint(1000, 9999))
        
        # Créer ou mettre à jour l'enregistrement OTP pour cet identifiant
        verification, created = OTPVerification.objects.update_or_create(
            identifier=identifier,
            defaults={
                'otp': otp,
                'created_at': timezone.now(),
                'is_verified': False
            }
        )
        
        # Envoyer l'OTP via le service de notification
        sms_message = f"""Votre code de vérification WOILA est : '{otp}'.
Il expire dans 5 minutes."""

        notification_result = NotificationService.send_otp(
            recipient=identifier,
            otp_code=otp,
            message=sms_message
        )
        
        # Log pour débogage
        logger.info(f"OTP send result for {identifier}: {notification_result}")
        
        # Réponse sans exposer l'OTP
        return Response({
            'message': 'Un code de vérification a été envoyé à votre numéro de téléphone.',
            'sms_sent': notification_result.get('success', False),
            'identifier': identifier
        })


class VerifyOTPView(APIView):
    """
    Vue pour vérifier un code OTP
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Vérifie un code OTP envoyé précédemment",
        request_body=OTPVerifySerializer,
        responses={
            200: openapi.Response(
                description="OTP vérifié avec succès",
                examples={
                    "application/json": {
                        "status": "verified",
                        "message": "Code OTP vérifié avec succès"
                    }
                }
            ),
            400: openapi.Response(
                description="OTP invalide ou expiré",
                examples={
                    "application/json": {
                        "error": "Code OTP invalide"
                    }
                }
            )
        },
        tags=['OTP']
    )
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        identifier = serializer.validated_data['identifier']
        otp_code = serializer.validated_data['otp']
        
        # Rechercher la vérification OTP
        verification = OTPVerification.objects.filter(
            identifier=identifier,
            otp=otp_code
        ).first()
        
        if not verification:
            return Response(
                {'error': 'Code OTP invalide'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not verification.is_valid():
            return Response(
                {'error': 'Code OTP expiré ou déjà utilisé'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Marquer l'OTP comme vérifié
        verification.is_verified = True
        verification.save()
        
        return Response({
            'status': 'verified',
            'message': 'Code OTP vérifié avec succès'
        })