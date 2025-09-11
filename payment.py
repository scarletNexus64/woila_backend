# api/views/payment.py

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
import logging
from django.urls import reverse
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from api.models import Package, PaymentTrx, ProfilePayment, Users
from api.serializers import PaymentTrxSerializer
from .freemopay import FreemoPayDirect

logger = logging.getLogger(__name__)

def normalize_phone_number(phone):
    """Normalise le numéro de téléphone pour FreeMoPay (retire le +)"""
    if phone and phone.startswith('+'):
        return phone[1:]
    return phone

def generate_simple_external_id(prefix="TRX"):
    """Génère un external_id simple et lisible pour USSD"""
    from django.utils import timezone
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    return f"{prefix}-{timestamp}"

def create_ussd_friendly_description(package_name, product_name=None):
    """Crée une description courte et claire pour l'affichage USSD"""
    if product_name:
        # Limiter à 30 caractères pour USSD
        return f"Premium {product_name[:20]}"
    else:
        return f"Achat {package_name[:20]}"

class ProcessPaymentView(APIView):
    """
    Vue qui initie un paiement FreeMoPay avec système de polling synchrone.
    Le paiement est bloquant jusqu'à obtention du statut final.
    """
    permission_classes = []
    @swagger_auto_schema(
        operation_description=(
            "Initie un paiement FreeMoPay avec polling synchrone.\n\n"
            "Cette API :\n"
            "1. Valide les données du paiement\n"
            "2. Initie le paiement avec FreeMoPay\n"
            "3. Effectue un polling toutes les secondes (max 2 minutes)\n"
            "4. Retourne le statut final du paiement\n\n"
            "**Important**: Cette API est bloquante et peut prendre jusqu'à 2 minutes."
        ),
        operation_summary="Traiter un paiement avec polling",
        tags=['Paiements'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['payer', 'amount', 'externalId', 'description', 'user_id', 'package_id'],
            properties={
                'payer': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='Numéro de téléphone du payeur (format: +243XXXXXXXXX)',
                    example='+243812345678'
                ),
                'amount': openapi.Schema(
                    type=openapi.TYPE_NUMBER, 
                    format=openapi.FORMAT_FLOAT, 
                    description='Montant à payer (doit correspondre au prix du package)',
                    example=50.0
                ),
                'externalId': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='Identifiant unique externe de la transaction',
                    example='TRX-2024-001'
                ),
                'description': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='Description du paiement',
                    example='Achat package Premium'
                ),
                'callback': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='URL de callback (optionnel, une URL par défaut sera utilisée)',
                    example='https://monsite.com/api/payment-callback'
                ),
                'user_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER, 
                    description='ID de l\'utilisateur effectuant le paiement',
                    example=123
                ),
                'package_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER, 
                    description='ID du package à acheter',
                    example=1
                ),
                'profile_payment_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER, 
                    description='ID du profil de paiement (optionnel)',
                    example=456
                ),
                'longitude': openapi.Schema(
                    type=openapi.TYPE_NUMBER, 
                    format=openapi.FORMAT_FLOAT, 
                    description='Longitude de la position du client',
                    example=-1.234567
                ),
                'latitude': openapi.Schema(
                    type=openapi.TYPE_NUMBER, 
                    format=openapi.FORMAT_FLOAT, 
                    description='Latitude de la position du client',
                    example=15.234567
                ),
                'city': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='Ville du client',
                    example='Kinshasa'
                ),
                'label': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='Nom personnalisé pour l\'espace de stockage (optionnel)',
                    example='Mon espace Pro'
                )
            }
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Paiement traité avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'payment': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description='Détails de la transaction créée'
                        ),
                        'freemo_response': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description='Réponse initiale de FreeMoPay',
                            properties={
                                'status': openapi.Schema(type=openapi.TYPE_STRING),
                                'reference': openapi.Schema(type=openapi.TYPE_STRING),
                                'external_id': openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        ),
                        'polling_result': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description='Résultat du polling',
                            properties={
                                'final_status': openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description='Statut final (SUCCESS, FAILED, CANCELLED, TIMEOUT)'
                                ),
                                'reason': openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description='Raison du statut'
                                ),
                                'duration': openapi.Schema(
                                    type=openapi.TYPE_NUMBER,
                                    description='Durée du polling en secondes'
                                ),
                                'attempts': openapi.Schema(
                                    type=openapi.TYPE_INTEGER,
                                    description='Nombre de tentatives de polling'
                                )
                            }
                        )
                    }
                ),
                examples={
                    'application/json': {
                        'payment': {
                            'id': 123,
                            'reference': '3803e924-3fb7-448f-9674-a3c2e20a10a8',
                            'status': 'success',
                            'amount': '50.00',
                            'created_at': '2024-01-15T10:30:00Z'
                        },
                        'freemo_response': {
                            'status': 'SUCCESS',
                            'reference': '3803e924-3fb7-448f-9674-a3c2e20a10a8',
                            'external_id': 'TRX-2024-001'
                        },
                        'polling_result': {
                            'final_status': 'SUCCESS',
                            'reason': 'Transaction completed.',
                            'duration': 15.3,
                            'attempts': 16
                        }
                    }
                }
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Données invalides ou erreur de paiement",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Message d\'erreur'
                        )
                    }
                ),
                examples={
                    'application/json': {
                        'error': 'Le montant demandé (100) ne correspond pas au prix du package (50). Paiement bloqué.'
                    }
                }
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Ressource non trouvée",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
                examples={
                    'application/json': {
                        'error': 'Utilisateur 999 non trouvé.'
                    }
                }
            )
        }
    )
    def post(self, request):
        try:
            data = request.data
            payer = normalize_phone_number(data.get('payer'))
            amount = data.get('amount')
            base_external_id = data.get('externalId') or generate_simple_external_id()
            description = data.get('description')
            
            # Assurer l'unicité de l'external_id
            external_id = base_external_id
            counter = 1
            while PaymentTrx.objects.filter(external_id=external_id).exists():
                if data.get('externalId'):  # Si fourni par l'utilisateur, ajouter timestamp
                    external_id = f"{base_external_id}-{generate_simple_external_id('').replace('TRX-', '')}"
                else:  # Si généré automatiquement, incrémenter
                    external_id = f"{base_external_id}-{counter}"
                    counter += 1
                logger.warning(f"[ProcessPayment] external_id {base_external_id} existe déjà, utilisation de {external_id}")
            callback = data.get('callback') or request.build_absolute_uri(reverse('payment-callback'))
            
            user_id = data.get('user_id')
            package_id = data.get('package_id')
            profile_payment_id = data.get('profile_payment_id')
            longitude = data.get('longitude')
            latitude = data.get('latitude')
            city = data.get('city')
            label = data.get('label')

            logger.info(f"[ProcessPayment] Nouvelle demande de paiement - User: {user_id}, Package: {package_id}, Montant: {amount}")

            # 1. Vérifier la présence des champs obligatoires
            if not all([payer, amount, external_id, description, callback, user_id, package_id]):
                logger.error("[ProcessPayment] Champs obligatoires manquants")
                return Response(
                    {
                        'error': (
                            'Les champs obligatoires (payer, amount, externalId, description, callback, '
                            'user_id, package_id) sont requis.'
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 2. Vérifier la validité des objets en base
            try:
                user = Users.objects.get(id=user_id)
                logger.debug(f"[ProcessPayment] Utilisateur trouvé: {user.email}")
            except Users.DoesNotExist:
                logger.error(f"[ProcessPayment] Utilisateur {user_id} non trouvé")
                return Response(
                    {'error': f'Utilisateur {user_id} non trouvé.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            try:
                package = Package.objects.get(package_id=package_id)
                logger.debug(f"[ProcessPayment] Package trouvé: {package.name} - Prix: {package.price}")
                # Créer une description optimisée pour USSD
                ussd_description = create_ussd_friendly_description(package.name)
            except Package.DoesNotExist:
                logger.error(f"[ProcessPayment] Package {package_id} non trouvé")
                return Response(
                    {'error': f'Package {package_id} non trouvé.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            profile_payment = None
            if profile_payment_id:
                try:
                    profile_payment = ProfilePayment.objects.get(id=profile_payment_id)
                    logger.debug(f"[ProcessPayment] Profil de paiement trouvé: {profile_payment_id}")
                except ProfilePayment.DoesNotExist:
                    logger.warning(f"[ProcessPayment] Profil de paiement {profile_payment_id} non trouvé")
                    return Response(
                        {'error': f'Profil de paiement {profile_payment_id} non trouvé.'},
                        status=status.HTTP_404_NOT_FOUND
                    )

            # 3. Vérifier que le montant correspond au prix du package
            package_price = float(package.price)
            if float(amount) != package_price:
                logger.error(f"[ProcessPayment] Montant incorrect - Demandé: {amount}, Prix package: {package_price}")
                return Response(
                    {
                        'error': (
                            f'Le montant demandé ({amount}) ne correspond pas au prix du package ({package_price}). '
                            'Paiement bloqué.'
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 4. Initier le paiement avec FreemoPayDirect
            logger.info(f"[ProcessPayment] Initialisation du paiement FreeMoPay...")
            freemo_response = FreemoPayDirect.init_payment(
                payer=payer,
                amount=float(amount),
                external_id=external_id,
                description=ussd_description,
                callback=callback
            )
            
            logger.debug(f"[ProcessPayment] Réponse init_payment: {freemo_response}")

            # 5. Vérifier si l'initialisation a réussi
            init_status = freemo_response.get('status')
            if init_status == 'FAILED':
                logger.error(f"[ProcessPayment] Échec de l'initialisation: {freemo_response.get('message')}")
                return Response(
                    {'error': freemo_response.get('message', 'Échec de paiement inconnu')},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Récupérer la référence
            reference = freemo_response.get('reference')
            if not reference:
                logger.error("[ProcessPayment] Pas de référence retournée par FreeMoPay")
                return Response(
                    {'error': 'Pas de référence de paiement retournée'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            logger.info(f"[ProcessPayment] Paiement initié avec succès - Référence: {reference}")
            
            # 6. NOUVEAU: Faire le polling pour obtenir le statut final
            logger.info(f"[ProcessPayment] Début du polling pour la référence: {reference}")
            polling_result = FreemoPayDirect.poll_payment_status(
                reference=reference,
                max_duration=120,  # 2 minutes
                interval=1  # 1 seconde
            )
            
            logger.info(f"[ProcessPayment] Résultat du polling: {polling_result.get('status')} après {polling_result.get('attempts')} tentatives")
            
            # 7. Déterminer le statut final de la transaction
            polling_status = polling_result.get('status')
            final_freemo_status = polling_result.get('final_status')
            
            if polling_status == 'SUCCESS':
                tx_status = 'success'
                logger.info(f"[ProcessPayment] ✅ Paiement confirmé avec succès")
            elif polling_status == 'FAILED':
                tx_status = 'error'
                logger.warning(f"[ProcessPayment] ❌ Paiement échoué/annulé - Raison: {polling_result.get('reason')}")
            elif polling_status == 'TIMEOUT':
                tx_status = 'timeout'
                logger.error(f"[ProcessPayment] ⏱️ Timeout du paiement après {polling_result.get('polling_duration')}s")
            else:
                tx_status = 'error'
                logger.error(f"[ProcessPayment] Statut inconnu: {polling_status}")
            
            # 8. Créer l'enregistrement PaymentTrx avec le statut final
            logger.info(f"[ProcessPayment] Création de la transaction en base avec statut: {tx_status}")
            payment_trx = PaymentTrx.objects.create(
                user=user,
                package=package,
                profile_payment=profile_payment,
                mobile_number=payer,
                external_id=external_id,
                amount=amount,
                description=description,
                status=tx_status,
                reference=reference,
                longitude=longitude,
                latitude=latitude,
                city=city,
                subscription_label=label
            )
            
            # 9. Si le paiement est réussi, mettre à jour les certifications
            if tx_status == 'success' and package:
                if package.is_certif_eco or package.is_certif_vip or package.is_certif_classic:
                    logger.info("[ProcessPayment] Mise à jour des certifications des produits...")
                    from api.views.subscription import update_product_certifications
                    update_product_certifications(user, package)

            # 10. Retourner la réponse avec tous les détails
            response_data = {
                'payment': PaymentTrxSerializer(payment_trx).data,
                'freemo_response': freemo_response,
                'polling_result': {
                    'final_status': polling_result.get('final_status'),
                    'reason': polling_result.get('reason'),
                    'duration': polling_result.get('polling_duration'),
                    'attempts': polling_result.get('attempts')
                }
            }
            
            logger.info(f"[ProcessPayment] Processus terminé - Transaction ID: {payment_trx.id}, Statut: {tx_status}")
            
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception("[ProcessPayment] Erreur inattendue lors du paiement")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class CheckPaymentStatusView(APIView):
    """
    Vue pour vérifier le statut d'un paiement à partir de sa référence.
    Utile pour vérifier manuellement ou pour des cas où le polling a timeout.
    """
    permission_classes = []
    
    @swagger_auto_schema(
        operation_description=(
            "Vérifie le statut actuel d'un paiement FreeMoPay.\n\n"
            "Utile pour :\n"
            "- Vérifier un paiement après un timeout\n"
            "- Obtenir le statut actuel d'une transaction\n"
            "- Mettre à jour le statut en base si nécessaire"
        ),
        operation_summary="Vérifier le statut d'un paiement",
        tags=['Paiements'],
        manual_parameters=[
            openapi.Parameter(
                'reference',
                openapi.IN_PATH,
                description='Référence unique du paiement retournée par FreeMoPay',
                type=openapi.TYPE_STRING,
                required=True,
                example='3803e924-3fb7-448f-9674-a3c2e20a10a8'
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Statut du paiement",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'payment_transaction': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description='Détails de la transaction en base'
                        ),
                        'freemo_status': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description='Statut actuel chez FreeMoPay',
                            properties={
                                'reference': openapi.Schema(type=openapi.TYPE_STRING),
                                'status': openapi.Schema(type=openapi.TYPE_STRING),
                                'reason': openapi.Schema(type=openapi.TYPE_STRING),
                                'amount': openapi.Schema(type=openapi.TYPE_NUMBER)
                            }
                        ),
                        'status_updated': openapi.Schema(
                            type=openapi.TYPE_BOOLEAN,
                            description='Indique si le statut a été mis à jour en base'
                        )
                    }
                )
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Transaction non trouvée",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur lors de la vérification",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        }
    )
    def get(self, request, reference):
        try:
            logger.info(f"[CheckPaymentStatus] Vérification du statut pour référence: {reference}")
            
            # 1. Récupérer la transaction dans la base
            try:
                payment_trx = PaymentTrx.objects.get(reference=reference)
                logger.debug(f"[CheckPaymentStatus] Transaction trouvée: ID={payment_trx.id}, Statut actuel={payment_trx.status}")
            except PaymentTrx.DoesNotExist:
                logger.error(f"[CheckPaymentStatus] Transaction non trouvée pour référence: {reference}")
                return Response(
                    {'error': f'Aucune transaction trouvée avec la référence {reference}'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 2. Obtenir le statut actuel depuis FreeMoPay
            payment_status = FreemoPayDirect.get_payment_status(reference)
            freemo_status = payment_status.get('status')
            
            logger.info(f"[CheckPaymentStatus] Statut FreeMoPay: {freemo_status}")
            
            # 3. Mettre à jour le statut en base si nécessaire
            status_updated = False
            old_status = payment_trx.status
            
            if freemo_status == 'SUCCESS' and payment_trx.status != 'success':
                payment_trx.status = 'success'
                payment_trx.save()
                status_updated = True
                logger.info(f"[CheckPaymentStatus] Statut mis à jour: {old_status} → success")
                
                # Mettre à jour les certifications si nécessaire
                if payment_trx.package and (payment_trx.package.is_certif_eco or 
                                        payment_trx.package.is_certif_vip or 
                                        payment_trx.package.is_certif_classic):
                    logger.info("[CheckPaymentStatus] Mise à jour des certifications...")
                    from api.views.subscription import update_product_certifications
                    update_product_certifications(payment_trx.user, payment_trx.package)
                    
            elif freemo_status == 'FAILED' and payment_trx.status != 'error':
                payment_trx.status = 'error'
                payment_trx.save()
                status_updated = True
                logger.info(f"[CheckPaymentStatus] Statut mis à jour: {old_status} → error")
                
            elif freemo_status == 'CANCELLED' and payment_trx.status != 'cancelled':
                payment_trx.status = 'cancelled'
                payment_trx.save()
                status_updated = True
                logger.info(f"[CheckPaymentStatus] Statut mis à jour: {old_status} → cancelled")
            
            # 4. Retourner les infos
            return Response({
                'payment_transaction': PaymentTrxSerializer(payment_trx).data,
                'freemo_status': payment_status,
                'status_updated': status_updated
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"[CheckPaymentStatus] Erreur: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class PaymentCallbackView(APIView):
    """
    Endpoint pour recevoir les callbacks de FreeMoPay.
    Maintenu pour compatibilité mais plus nécessaire avec le polling.
    """
    permission_classes = []  # Pas d'authentification requise pour les callbacks
    
    def post(self, request):
        try:
            # Récupérer les données envoyées par FreeMoPay
            data = request.data
            reference = data.get('reference')
            status_value = data.get('status')
            reason = data.get('reason')
            
            logger.info(f"[PaymentCallback] Callback reçu - Référence: {reference}, Statut: {status_value}, Raison: {reason}")
            
            if not reference:
                return Response({'error': 'Référence manquante'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Mettre à jour la transaction en base de données
            try:
                payment_trx = PaymentTrx.objects.get(reference=reference)
                old_status = payment_trx.status
                
                # Ne mettre à jour que si le statut est différent
                if status_value == 'SUCCESS' and payment_trx.status != 'success':
                    payment_trx.status = 'success'
                    payment_trx.save()
                    logger.info(f"[PaymentCallback] Statut mis à jour via callback: {old_status} → success")
                    
                    # Mettre à jour les certifications si nécessaire
                    if payment_trx.package and (payment_trx.package.is_certif_eco or 
                                            payment_trx.package.is_certif_vip or 
                                            payment_trx.package.is_certif_classic):
                        from api.views.subscription import update_product_certifications
                        update_product_certifications(payment_trx.user, payment_trx.package)
                        
                elif status_value == 'FAILED' and payment_trx.status != 'error':
                    payment_trx.status = 'error'
                    payment_trx.save()
                    logger.info(f"[PaymentCallback] Statut mis à jour via callback: {old_status} → error")
                    
                elif status_value == 'CANCELLED' and payment_trx.status != 'cancelled':
                    payment_trx.status = 'cancelled'
                    payment_trx.save()
                    logger.info(f"[PaymentCallback] Statut mis à jour via callback: {old_status} → cancelled")
                
                return Response({'status': 'success'}, status=status.HTTP_200_OK)
                
            except PaymentTrx.DoesNotExist:
                logger.error(f"[PaymentCallback] Transaction non trouvée pour référence: {reference}")
                return Response(
                    {'error': f'Transaction non trouvée pour la référence {reference}'},
                    status=status.HTTP_404_NOT_FOUND
                )
                
        except Exception as e:
            logger.error(f"[PaymentCallback] Erreur: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentListView(APIView):
    """
    Vue pour récupérer la liste de tous les paiements
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Récupérer les paiements de l'utilisateur
            payments = PaymentTrx.objects.filter(user=request.user).order_by('-created_at')
            serializer = PaymentTrxSerializer(payments, many=True)
            
            logger.info(f"[PaymentList] {len(payments)} paiements trouvés pour user: {request.user.id}")
            
            return Response({
                'count': len(payments),
                'payments': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"[PaymentList] Erreur: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class UserPaymentListView(APIView):
    """
    Vue pour récupérer la liste des paiements d'un utilisateur spécifique
    """
    permission_classes = [IsAuthenticated]
    def get(self, request, user_id):
        try:
            # Vérifier si l'utilisateur existe
            try:
                user = Users.objects.get(id=user_id)
            except Users.DoesNotExist:
                return Response(
                    {'error': f"Utilisateur avec l'ID {user_id} non trouvé"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Vérifier les permissions - seul l'utilisateur lui-même ou un admin peut voir
            if request.user.id != user.id and not request.user.is_staff:
                return Response(
                    {'error': "Vous n'êtes pas autorisé à accéder aux paiements de cet utilisateur"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Récupérer les paiements
            payments = PaymentTrx.objects.filter(user=user).order_by('-created_at')
            
            # Sérialiser et retourner
            serializer = PaymentTrxSerializer(payments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    """
    Vue pour récupérer la liste des paiements d'un utilisateur spécifique
    """
    permission_classes = [IsAuthenticated]
    def get(self, request, user_id):
        try:
            # Vérifier si l'utilisateur existe
            try:
                user = Users.objects.get(id=user_id)
            except Users.DoesNotExist:
                return Response(
                    {'error': f"Utilisateur avec l'ID {user_id} non trouvé"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Vérifier les permissions - seul l'utilisateur lui-même ou un admin peut voir
            if request.user.id != user.id and not request.user.is_staff:
                return Response(
                    {'error': "Vous n'êtes pas autorisé à accéder aux paiements de cet utilisateur"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Récupérer les paiements
            payments = PaymentTrx.objects.filter(user=user).order_by('-created_at')
            
            # Sérialiser et retourner
            serializer = PaymentTrxSerializer(payments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
