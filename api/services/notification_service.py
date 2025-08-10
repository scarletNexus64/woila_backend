# api/services/notification_service.py
import logging
from typing import Dict, Any, Optional
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from ..models import NotificationConfig, Notification, UserDriver, UserCustomer, Wallet, GeneralConfig
from .nexah_service import NexahService
from .whatsapp_service import WhatsAppService
from .fcm_service import FCMService

logger = logging.getLogger(__name__)

class NotificationService:
    """Unified service for sending notifications via SMS or WhatsApp"""
    
    @classmethod
    def send_otp(cls, recipient, otp_code, message=None, channel=None):
        """
        Send OTP code via the configured notification channel
        
        Args:
            recipient: Phone number to send to
            otp_code: The OTP code to send
            message: Custom message (for SMS)
            channel: Force specific channel ('sms' or 'whatsapp')
        
        Returns:
            dict: Response with success status and details
        """
        try:
            # Get configuration
            config = NotificationConfig.get_config()
            
            # Use provided channel or fall back to config default
            channel = channel or config.default_channel
            
            if channel == 'whatsapp':
                # Send via WhatsApp
                return WhatsAppService.send_otp(
                    recipient=recipient,
                    otp_code=otp_code
                )
            else:
                # Send via SMS (default)
                sms_message = message or f"""Votre code de vérification WOILA est : '{otp_code}'.
Il expire dans 5 minutes."""
                
                return NexahService.send_sms(
                    recipient=recipient,
                    message=sms_message
                )
                
        except Exception as e:
            logger.error(f"Error in NotificationService.send_otp: {str(e)}")
            return {
                'success': False,
                'message': f'Service error: {str(e)}',
                'data': None
            }
    
    @classmethod
    def send_message(cls, recipient, message, channel=None):
        """
        Send a generic message via the configured notification channel
        
        Args:
            recipient: Phone number to send to
            message: Message content
            channel: Force specific channel ('sms' or 'whatsapp')
        
        Returns:
            dict: Response with success status and details
        """
        try:
            # Get configuration
            config = NotificationConfig.get_config()
            
            # Use provided channel or fall back to config default
            channel = channel or config.default_channel
            
            if channel == 'whatsapp':
                # For WhatsApp, we'd need a generic message template
                # For now, fallback to SMS for generic messages
                logger.warning(f"WhatsApp generic messages not implemented, falling back to SMS")
                return NexahService.send_sms(
                    recipient=recipient,
                    message=message
                )
            else:
                # Send via SMS
                return NexahService.send_sms(
                    recipient=recipient,
                    message=message
                )
                
        except Exception as e:
            logger.error(f"Error in NotificationService.send_message: {str(e)}")
            return {
                'success': False,
                'message': f'Service error: {str(e)}',
                'data': None
            }
    
    # ===== NOUVELLES MÉTHODES POUR NOTIFICATIONS UTILISATEURS =====
    
    @classmethod
    def create_notification(cls, user, title: str, content: str, 
                          notification_type: str = 'system', 
                          metadata: Optional[Dict[str, Any]] = None) -> Optional[Notification]:
        """
        Crée une nouvelle notification pour un utilisateur
        
        Args:
            user: Instance UserDriver ou UserCustomer
            title: Titre de la notification
            content: Contenu de la notification
            notification_type: Type de notification
            metadata: Métadonnées supplémentaires
        
        Returns:
            Instance Notification créée ou None en cas d'erreur
        """
        try:
            # Obtenir le ContentType approprié
            content_type = ContentType.objects.get_for_model(user)
            
            # Créer la notification
            notification = Notification.objects.create(
                user_type=content_type,
                user_id=user.id,
                title=title,
                content=content,
                notification_type=notification_type,
                metadata=metadata or {}
            )
            
            logger.info(f"Notification créée: {title} pour {user.name} {user.surname}")
            return notification
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de notification: {str(e)}")
            return None
    
    @classmethod
    def send_welcome_notification(cls, user) -> bool:
        """
        Envoie une notification de bienvenue à un nouvel utilisateur
        
        Args:
            user: Instance UserDriver ou UserCustomer
            
        Returns:
            True si succès, False sinon
        """
        try:
            user_type = "chauffeur" if isinstance(user, UserDriver) else "client"
            
            title = f"🎉 Bienvenue sur WOILA !"
            content = f"""Bonjour {user.name},

Bienvenue dans la famille WOILA ! Nous sommes ravis de vous accueillir en tant que {user_type}.

🚀 Votre aventure commence maintenant ! Découvrez toutes les fonctionnalités de notre plateforme et profitez d'une expérience de transport moderne et sécurisée.

L'équipe WOILA vous souhaite la bienvenue ! 🤝"""

            metadata = {
                'user_type': user_type,
                'registration_date': timezone.now().isoformat(),
                'phone_number': user.phone_number
            }
            
            notification = cls.create_notification(
                user=user,
                title=title,
                content=content,
                notification_type='welcome',
                metadata=metadata
            )
            
            if notification:
                # Envoyer également via FCM (notification push)
                fcm_success = FCMService.send_welcome_notification(user)
                
                logger.info(f"Notification de bienvenue envoyée à {user.name} {user.surname} - DB: ✅ FCM: {'✅' if fcm_success else '❌'}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de notification de bienvenue: {str(e)}")
            return False
    
    @classmethod
    def send_referral_bonus_notification(cls, referrer_user, referred_user, referral_code: str, bonus_amount: float) -> bool:
        """
        Envoie une notification au propriétaire d'un code parrain utilisé + bonus wallet
        
        Args:
            referrer_user: Utilisateur propriétaire du code parrain
            referred_user: Utilisateur qui a utilisé le code
            referral_code: Code parrain utilisé
            bonus_amount: Montant du bonus accordé
            
        Returns:
            True si succès, False sinon
        """
        try:
            # Ajouter le bonus au wallet du parrain
            content_type = ContentType.objects.get_for_model(referrer_user)
            wallet, created = Wallet.objects.get_or_create(
                user_type=content_type,
                user_id=referrer_user.id,
                defaults={'balance': bonus_amount}
            )
            
            if not created:
                wallet.balance += bonus_amount
                wallet.save()
            
            # Créer la notification
            title = f"🎁 Code parrain utilisé !"
            content = f"""Excellente nouvelle {referrer_user.name} !

Votre code parrain "{referral_code}" a été utilisé par {referred_user.name} {referred_user.surname}.

💰 Vous avez reçu un bonus de {bonus_amount} FCFA dans votre portefeuille !

Nouveau solde: {wallet.balance} FCFA

Merci de faire grandir la communauté WOILA ! 🚀"""

            metadata = {
                'referral_code': referral_code,
                'referred_user_id': referred_user.id,
                'referred_user_name': f"{referred_user.name} {referred_user.surname}",
                'bonus_amount': bonus_amount,
                'new_balance': float(wallet.balance)
            }
            
            notification = cls.create_notification(
                user=referrer_user,
                title=title,
                content=content,
                notification_type='referral_used',
                metadata=metadata
            )
            
            if notification:
                # Envoyer également via FCM (notification push)
                fcm_success = FCMService.send_referral_bonus_notification(
                    user=referrer_user,
                    referral_code=referral_code,
                    bonus_amount=bonus_amount
                )
                
                logger.info(f"Notification de parrainage envoyée à {referrer_user.name} - Bonus: {bonus_amount} FCFA - DB: ✅ FCM: {'✅' if fcm_success else '❌'}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de notification de parrainage: {str(e)}")
            return False
    
    @classmethod
    def send_vehicle_approval_notification(cls, driver, vehicle) -> bool:
        """
        Envoie une notification d'approbation de véhicule au chauffeur
        
        Args:
            driver: Instance UserDriver
            vehicle: Instance Vehicle approuvée
            
        Returns:
            True si succès, False sinon
        """
        try:
            title = f"🚗✅ Véhicule approuvé !"
            content = f"""Félicitations {driver.name} !

Votre véhicule "{vehicle.nom}" ({vehicle.brand} {vehicle.model}) a été approuvé par notre équipe.

📋 Détails du véhicule:
• Marque: {vehicle.brand}
• Modèle: {vehicle.model}
• Plaque: {vehicle.plaque_immatriculation}
• État: {vehicle.get_etat_display_short()}

Vous pouvez désormais commencer à opérer avec ce véhicule ! 🎉

Bonne route avec WOILA ! 🛣️"""

            metadata = {
                'vehicle_id': vehicle.id,
                'vehicle_name': vehicle.nom,
                'vehicle_brand': str(vehicle.brand),
                'vehicle_model': str(vehicle.model),
                'license_plate': vehicle.plaque_immatriculation,
                'vehicle_state': vehicle.etat_vehicule,
                'approval_date': timezone.now().isoformat()
            }
            
            notification = cls.create_notification(
                user=driver,
                title=title,
                content=content,
                notification_type='vehicle_approved',
                metadata=metadata
            )
            
            if notification:
                # Envoyer également via FCM (notification push)
                fcm_success = FCMService.send_vehicle_approval_notification(
                    driver=driver,
                    vehicle_name=vehicle.nom
                )
                
                logger.info(f"Notification d'approbation véhicule envoyée à {driver.name} pour {vehicle.nom} - DB: ✅ FCM: {'✅' if fcm_success else '❌'}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de notification d'approbation véhicule: {str(e)}")
            return False
    
    @classmethod
    def get_user_notifications(cls, user, include_read: bool = True, include_deleted: bool = False) -> list:
        """
        Récupère les notifications d'un utilisateur
        
        Args:
            user: Instance UserDriver ou UserCustomer
            include_read: Inclure les notifications lues
            include_deleted: Inclure les notifications supprimées
            
        Returns:
            Liste des notifications
        """
        try:
            content_type = ContentType.objects.get_for_model(user)
            
            queryset = Notification.objects.filter(
                user_type=content_type,
                user_id=user.id
            )
            
            if not include_read:
                queryset = queryset.filter(is_read=False)
            
            if not include_deleted:
                queryset = queryset.filter(is_deleted=False)
            
            return list(queryset.order_by('-created_at'))
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des notifications: {str(e)}")
            return []
    
    @classmethod
    def get_unread_count(cls, user) -> int:
        """
        Compte les notifications non lues d'un utilisateur
        
        Args:
            user: Instance UserDriver ou UserCustomer
            
        Returns:
            Nombre de notifications non lues
        """
        try:
            content_type = ContentType.objects.get_for_model(user)
            
            return Notification.objects.filter(
                user_type=content_type,
                user_id=user.id,
                is_read=False,
                is_deleted=False
            ).count()
            
        except Exception as e:
            logger.error(f"Erreur lors du comptage des notifications non lues: {str(e)}")
            return 0