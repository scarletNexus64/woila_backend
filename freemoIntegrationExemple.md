# api/freemopay.py
import requests
import json
import logging
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class FreemoPayDirect:
    """Implémentation directe de l'API FreeMo Pay avec système de polling."""
    
    # Configuration
    BASE_URL = "https://api-v2.freemopay.com/api/v2"
    APP_KEY = "8381e965-51e0-42bd-b260-a78d9affa316"
    SECRET_KEY = "hBbdnuQc3wlIch8HkuPb"
    REQUEST_TIMEOUT = 30  # secondes
    
    # Configuration du polling
    POLLING_INTERVAL = 1  # secondes entre chaque vérification
    POLLING_MAX_DURATION = 120  # 2 minutes maximum
    
    @classmethod
    def _log_request(cls, method, url, headers=None, payload=None):
        """Log les détails de la requête pour le débogage"""
        logger.debug(f"[FreeMoPay] {method} {url}")
        if headers:
            # Masquer les informations sensibles dans les en-têtes
            safe_headers = headers.copy()
            if 'Authorization' in safe_headers:
                safe_headers['Authorization'] = 'Bearer [HIDDEN]'
            logger.debug(f"[FreeMoPay] Headers: {safe_headers}")
        if payload:
            # Masquer les informations sensibles dans le payload
            safe_payload = payload.copy() if isinstance(payload, dict) else payload
            if isinstance(safe_payload, dict) and 'secretKey' in safe_payload:
                safe_payload['secretKey'] = '[HIDDEN]'
            logger.debug(f"[FreeMoPay] Payload: {safe_payload}")
    
    @classmethod
    def generate_token(cls):
        """Génère un token d'authentification FreeMo Pay"""
        url = f"{cls.BASE_URL}/payment/token"
        
        payload = {
            "appKey": cls.APP_KEY,
            "secretKey": cls.SECRET_KEY
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        cls._log_request("POST", url, headers, {"appKey": payload["appKey"], "secretKey": "[HIDDEN]"})
        
        try:
            payload_json = json.dumps(payload)
            response = requests.request(
                "POST", 
                url, 
                headers=headers, 
                data=payload_json,
                timeout=cls.REQUEST_TIMEOUT
            )
            
            logger.debug(f"[FreeMoPay] Response status: {response.status_code}")
            logger.debug(f"[FreeMoPay] Response body: {response.text[:200]}...")
            
            if response.status_code == 200:
                token_data = response.json()
                return token_data.get('access_token')
            else:
                logger.error(f"[FreeMoPay] Erreur de réponse: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"[FreeMoPay] Timeout lors de la génération du token (>{cls.REQUEST_TIMEOUT}s)")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"[FreeMoPay] Erreur de connexion: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"[FreeMoPay] Erreur inattendue: {str(e)}")
            return None

    @classmethod
    def init_payment(cls, payer, amount, external_id, description, callback):
        """
        Initialise un paiement FreeMo Pay.
        IMPORTANT: Le statut 'SUCCESS' retourné indique seulement que la demande 
        a été initiée, pas que le paiement est complété.
        """
        # Génération du token
        token = cls.generate_token()
        if not token:
            return {'status': 'FAILED', 'message': 'Échec de génération du token d\'authentification'}
        
        url = f"{cls.BASE_URL}/payment"
        
        payload = {
            "payer": payer,
            "amount": amount,
            "externalId": external_id,
            "description": description,
            "callback": callback
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        # Log la requête
        cls._log_request("POST", url, headers, payload)
        
        try:
            # Convertir le payload en JSON
            payload_json = json.dumps(payload)
            
            # Utiliser exactement la méthode de l'exemple
            response = requests.request(
                "POST", 
                url, 
                headers=headers, 
                data=payload_json,
                timeout=cls.REQUEST_TIMEOUT
            )
            
            # Log la réponse
            logger.debug(f"[FreeMoPay] Response status: {response.status_code}")
            logger.debug(f"[FreeMoPay] Response body: {response.text[:200]}...")
            
            # Vérifier si la réponse est valide
            if response.status_code == 200:
                result = response.json()
                result['external_id'] = external_id
                logger.info(f"[FreeMoPay] Paiement initié avec succès - Référence: {result.get('reference')}")
                return result
            else:
                logger.error(f"[FreeMoPay] Erreur de réponse: {response.status_code} - {response.text}")
                return {'status': 'FAILED', 'message': f'Erreur HTTP {response.status_code}', 'external_id': external_id}
                
        except requests.exceptions.Timeout:
            logger.error(f"[FreeMoPay] Timeout lors de l'initialisation du paiement (>{cls.REQUEST_TIMEOUT}s)")
            return {'status': 'FAILED', 'message': 'Timeout de la requête', 'external_id': external_id}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"[FreeMoPay] Erreur de connexion: {str(e)}")
            return {'status': 'FAILED', 'message': f'Erreur de connexion: {str(e)}', 'external_id': external_id}
        except Exception as e:
            logger.error(f"[FreeMoPay] Erreur inattendue: {str(e)}")
            return {'status': 'FAILED', 'message': f'Erreur: {str(e)}', 'external_id': external_id}
    
    @classmethod
    def get_payment_status(cls, reference):
        """Obtenir le statut d'un paiement par référence"""
        # Génération du token
        token = cls.generate_token()
        if not token:
            return {'status': 'FAILED', 'message': 'Échec de génération du token d\'authentification'}
        
        url = f"{cls.BASE_URL}/payment/{reference}"
        
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        # Log la requête
        cls._log_request("GET", url, headers)
        
        try:
            # Utiliser exactement la méthode de l'exemple
            response = requests.request(
                "GET", 
                url, 
                headers=headers, 
                data={},
                timeout=cls.REQUEST_TIMEOUT
            )
            
            # Log la réponse
            logger.debug(f"[FreeMoPay] Response status: {response.status_code}")
            logger.debug(f"[FreeMoPay] Response body: {response.text[:200]}...")
            
            # Vérifier si la réponse est valide
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"[FreeMoPay] Erreur de réponse: {response.status_code} - {response.text}")
                return {'status': 'FAILED', 'message': f'Erreur HTTP {response.status_code}'}
                
        except requests.exceptions.Timeout:
            logger.error(f"[FreeMoPay] Timeout lors de la récupération du statut (>{cls.REQUEST_TIMEOUT}s)")
            return {'status': 'FAILED', 'message': 'Timeout de la requête'}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"[FreeMoPay] Erreur de connexion: {str(e)}")
            return {'status': 'FAILED', 'message': f'Erreur de connexion: {str(e)}'}
        except Exception as e:
            logger.error(f"[FreeMoPay] Erreur inattendue: {str(e)}")
            return {'status': 'FAILED', 'message': f'Erreur: {str(e)}'}
    
    @classmethod
    def poll_payment_status(cls, reference, max_duration=None, interval=None):
        """
        Fait du polling sur le statut d'un paiement jusqu'à obtenir SUCCESS/FAILED ou timeout.
        
        Args:
            reference: La référence du paiement
            max_duration: Durée max en secondes (défaut: 120s = 2min)
            interval: Intervalle entre chaque vérification en secondes (défaut: 1s)
        
        Returns:
            dict avec le statut final et les détails
        """
        if max_duration is None:
            max_duration = cls.POLLING_MAX_DURATION
        if interval is None:
            interval = cls.POLLING_INTERVAL
            
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=max_duration)
        attempt = 0
        
        logger.info(f"[FreeMoPay Polling] Début du polling pour la référence: {reference}")
        logger.info(f"[FreeMoPay Polling] Durée max: {max_duration}s, Intervalle: {interval}s")
        
        while datetime.now() < end_time:
            attempt += 1
            elapsed = (datetime.now() - start_time).total_seconds()
            
            logger.debug(f"[FreeMoPay Polling] Tentative #{attempt} - Temps écoulé: {elapsed:.1f}s")
            
            try:
                # Obtenir le statut actuel
                status_response = cls.get_payment_status(reference)
                current_status = status_response.get('status', 'UNKNOWN')
                reason = status_response.get('reason', '')
                
                logger.info(f"[FreeMoPay Polling] Statut actuel: {current_status} - Raison: {reason}")
                
                # Vérifier si on a un statut final
                if current_status == 'SUCCESS':
                    logger.info(f"[FreeMoPay Polling] ✅ Paiement confirmé après {elapsed:.1f}s")
                    return {
                        'status': 'SUCCESS',
                        'final_status': current_status,
                        'reason': reason,
                        'polling_duration': elapsed,
                        'attempts': attempt,
                        'reference': reference,
                        'full_response': status_response
                    }
                    
                elif current_status == 'FAILED' or current_status == 'CANCELLED':
                    logger.warning(f"[FreeMoPay Polling] ❌ Paiement échoué/annulé après {elapsed:.1f}s - Raison: {reason}")
                    return {
                        'status': 'FAILED',
                        'final_status': current_status,
                        'reason': reason,
                        'polling_duration': elapsed,
                        'attempts': attempt,
                        'reference': reference,
                        'full_response': status_response
                    }
                
                elif current_status in ['PENDING', 'CREATED']:
                    # CREATED = transaction créée mais pas encore traitée, traiter comme PENDING
                    # Continuer le polling
                    logger.debug(f"[FreeMoPay Polling] Statut {current_status}, attente de {interval}s...")
                    time.sleep(interval)
                    
                else:
                    # Statut inconnu
                    logger.error(f"[FreeMoPay Polling] Statut inconnu reçu: {current_status}")
                    return {
                        'status': 'FAILED',
                        'final_status': current_status,
                        'reason': f'Statut inconnu: {current_status}',
                        'polling_duration': elapsed,
                        'attempts': attempt,
                        'reference': reference,
                        'full_response': status_response
                    }
                    
            except Exception as e:
                logger.error(f"[FreeMoPay Polling] Erreur lors de la tentative #{attempt}: {str(e)}")
                # On continue le polling malgré l'erreur
                time.sleep(interval)
        
        # Timeout atteint
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error(f"[FreeMoPay Polling] ⏱️ Timeout atteint après {elapsed:.1f}s et {attempt} tentatives")
        
        # Faire une dernière vérification
        try:
            final_status = cls.get_payment_status(reference)
            return {
                'status': 'TIMEOUT',
                'final_status': final_status.get('status', 'UNKNOWN'),
                'reason': f'Timeout après {max_duration}s',
                'polling_duration': elapsed,
                'attempts': attempt,
                'reference': reference,
                'full_response': final_status
            }
        except:
            return {
                'status': 'TIMEOUT',
                'final_status': 'UNKNOWN',
                'reason': f'Timeout après {max_duration}s',
                'polling_duration': elapsed,
                'attempts': attempt,
                'reference': reference,
                'full_response': None
            }


