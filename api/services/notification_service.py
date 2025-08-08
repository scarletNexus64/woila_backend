# api/services/notification_service.py
import logging
from ..models import NotificationConfig
from .nexah_service import NexahService
from .whatsapp_service import WhatsAppService

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