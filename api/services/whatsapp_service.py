# api/services/whatsapp_service.py
import requests
import logging
from ..models import NotificationConfig

logger = logging.getLogger(__name__)

class WhatsAppService:
    """Service to handle WhatsApp communications with Meta API"""
    
    @classmethod
    def send_otp(cls, recipient, otp_code, template_name=None, language_code=None):
        """
        Send OTP via WhatsApp using a template
        
        Args:
            recipient: Recipient phone number (format: +237658895572)
            otp_code: The OTP code to send
            template_name: Optional WhatsApp template name (overrides config)
            language_code: Optional template language code (overrides config)
        
        Returns:
            dict: Response with success status and details
        """
        try:
            # Get configuration
            config = NotificationConfig.get_config()
            
            # Use provided template/language or fall back to config
            template_name = template_name or config.whatsapp_template_name
            language_code = language_code or config.whatsapp_language
            
            # Build API URL from configuration
            base_url = f'https://graph.facebook.com/{config.whatsapp_api_version}/{config.whatsapp_phone_number_id}/messages'
            
            # Normalize phone number to include + if missing
            if not recipient.startswith('+'):
                recipient = f'+{recipient}'
            
            # Prepare request payload
            payload = {
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": language_code
                    },
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {
                                    "type": "text",
                                    "text": str(otp_code)
                                }
                            ]
                        },
                        {
                            "type": "button",
                            "sub_type": "url",
                            "index": 0,
                            "parameters": [
                                {
                                    "type": "text",
                                    "text": str(otp_code)
                                }
                            ]
                        }
                    ]
                }
            }
            
            # Set headers with token from configuration
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {config.whatsapp_api_token}'
            }
            
            # Debug logging
            logger.info(f"Sending WhatsApp OTP to {recipient}")
            logger.debug(f"WhatsApp API URL: {base_url}")
            logger.debug(f"WhatsApp API payload template: {template_name}")
            
            # Send request
            response = requests.post(base_url, json=payload, headers=headers)
            
            # Log response
            logger.info(f"WhatsApp API response status: {response.status_code}")
            logger.debug(f"WhatsApp API response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for successful message acceptance
                if data.get('messages') and len(data['messages']) > 0:
                    message_status = data['messages'][0].get('message_status')
                    message_id = data['messages'][0].get('id')
                    
                    if message_status == 'accepted':
                        return {
                            'success': True,
                            'message': 'WhatsApp message accepted',
                            'message_id': message_id,
                            'data': data
                        }
                
                # If we can't confirm success from response
                return {
                    'success': False,
                    'message': 'WhatsApp message sent but status unclear',
                    'data': data
                }
            
            return {
                'success': False,
                'message': f'Server error: {response.status_code}',
                'data': response.text
            }
            
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'data': None
            }