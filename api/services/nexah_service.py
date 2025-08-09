# api/services/nexah_service.py
import requests
import logging
from ..models import NotificationConfig

logger = logging.getLogger(__name__)

class NexahService:
    """Service to handle SMS communications with Nexah API"""
    
    @classmethod
    def send_sms(cls, recipient, message, sender_id=None):
        """
        Send SMS via Nexah API
        
        Args:
            recipient: Recipient phone number
            message: SMS content
            sender_id: Optional sender ID (if none, uses configured sender)
        
        Returns:
            dict: Response with success status and details
        """
        try:
            # Get configuration
            config = NotificationConfig.get_config()
            
            # Build URL from configuration
            url = f"{config.nexah_base_url}{config.nexah_send_endpoint}"
            
            # Prepare request payload with config values
            payload = {
                'user': config.nexah_user,
                'password': config.nexah_password,
                'senderid': sender_id or config.nexah_sender_id,
                'sms': message,
                'mobiles': recipient,
            }
            
            # Set headers
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            }
            
            # Debug logging
            logger.info(f"Sending SMS to {recipient}")
            logger.debug(f"Nexah API URL: {url}")
            logger.debug(f"Nexah API payload user: {payload['user']}, sender: {payload['senderid']}")
            
            # Send request
            response = requests.post(url, json=payload, headers=headers)
            
            # Log response
            logger.info(f"Nexah API response: {response.status_code}")
            logger.debug(f"Nexah API response text: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse different success response formats
                is_success = False
                message = 'SMS sending failed'
                
                if data.get('status') in ['success', 'ok']:
                    is_success = True
                    message = 'SMS sent successfully!'
                elif data.get('sent') is True:
                    is_success = True
                    message = 'SMS sent successfully!'
                elif data.get('error') is False:
                    is_success = True
                    message = 'SMS sent successfully!'
                elif data.get('response') in ['OK'] or 'success' in str(data.get('response', '')).lower():
                    is_success = True
                    message = 'SMS sent successfully!'
                elif 'success' in str(data).lower() or 'ok' in str(data).lower():
                    is_success = True
                    message = 'SMS sent successfully!'
                
                return {
                    'success': is_success,
                    'message': message,
                    'data': data
                }
            
            return {
                'success': False,
                'message': f'Server error: {response.status_code}',
                'data': None
            }
        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'data': None
            }
    
    @classmethod
    def get_account_info(cls):
        """
        Get account information including credit balance
        
        Returns:
            dict: Account information including credit balance
        """
        try:
            # Get configuration
            config = NotificationConfig.get_config()
            
            # Build URL from configuration
            url = f"{config.nexah_base_url}{config.nexah_credits_endpoint}"
            
            # Prepare request payload
            payload = {
                'user': config.nexah_user,
                'password': config.nexah_password,
            }
            
            # Set headers
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            }
            
            # Send request
            response = requests.post(url, json=payload, headers=headers)
            
            logger.info(f"Account info response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                credit = None
                
                # Extract credit balance from different response structures
                if isinstance(data, dict):
                    if 'credit' in data:
                        credit = data['credit']
                    elif 'data' in data and isinstance(data['data'], dict):
                        credit = data['data'].get('credit') or data['data'].get('balance')
                    elif 'response' in data and isinstance(data['response'], dict):
                        credit = data['response'].get('credit') or data['response'].get('balance')
                
                return {
                    'success': True,
                    'credit': credit,
                    'user': config.nexah_user,
                    'sender_id': config.nexah_sender_id,
                    'data': data
                }
            
            return {
                'success': False,
                'message': f'Server error: {response.status_code}',
                'data': None
            }
        except Exception as e:
            logger.error(f"Error getting account info: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'data': None
            }