"""
Service Firebase Cloud Messaging pour l'envoi de notifications push
Utilise OAuth2 avec Service Account (méthode moderne et sécurisée)
"""
import json
import time
import logging
import traceback
import jwt
import requests
from typing import List, Dict, Optional, Union
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from ..models import NotificationConfig, FCMToken, Notification
from applications.users.models import UserDriver, UserCustomer


logger = logging.getLogger(__name__)


class FCMService:
    """
    Service pour gérer Firebase Cloud Messaging avec OAuth2
    """
    
    FCM_API_URL = "https://fcm.googleapis.com/v1/projects/{}/messages:send"
    OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
    
    @classmethod
    def get_firebase_oauth2_token(cls) -> Optional[str]:
        """Obtient un token OAuth2 pour l'authentification Firebase API"""
        try:
            service_account_path = settings.FCM_SERVICE_ACCOUNT_PATH
            
            with open(service_account_path, 'r') as f:
                service_account = json.load(f)
            
            # Créer le payload JWT
            payload = {
                'iss': service_account['client_email'],
                'sub': service_account['client_email'], 
                'aud': cls.OAUTH_TOKEN_URL,
                'iat': int(time.time()),
                'exp': int(time.time()) + 3600,
                'scope': 'https://www.googleapis.com/auth/firebase.messaging'
            }
            
            # Encoder le JWT
            encoded_jwt = jwt.encode(
                payload,
                service_account['private_key'],
                algorithm='RS256'
            )
            
            # Échanger le JWT contre un token OAuth2
            response = requests.post(
                cls.OAUTH_TOKEN_URL,
                data={
                    'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
                    'assertion': encoded_jwt
                }
            )
            
            if response.status_code == 200:
                oauth2_token = response.json().get('access_token')
                logger.debug("Token OAuth2 Firebase obtenu avec succès")
                return oauth2_token
            else:
                logger.error(f"Erreur token OAuth2: {response.status_code}, {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de l'obtention du token OAuth2: {str(e)}")
            return None
    
    @classmethod
    def register_token(cls, user: Union[UserDriver, UserCustomer], 
                      token: str, device_info: Dict) -> FCMToken:
        """
        Enregistre un token FCM pour un utilisateur
        """
        try:
            # Déterminer le type d'utilisateur et content type
            content_type = ContentType.objects.get_for_model(user)
            
            # Extraire les infos de l'appareil
            platform = device_info.get('platform', 'unknown')
            device_id = device_info.get('device_id', f"{platform}-{timezone.now().timestamp()}")
            
            # Vérifier si le token existe déjà (chercher d'abord par token pour éviter les conflits unique)
            try:
                fcm_token = FCMToken.objects.get(token=token)
                # Token existe déjà, mettre à jour les infos utilisateur et appareil
                fcm_token.user_type = content_type
                fcm_token.user_id = user.id
                fcm_token.device_id = device_id
                fcm_token.platform = platform
                fcm_token.device_info = device_info
                fcm_token.is_active = True
                fcm_token.save()
                created = False
            except FCMToken.DoesNotExist:
                # Token n'existe pas, le créer
                fcm_token = FCMToken.objects.create(
                    user_type=content_type,
                    user_id=user.id,
                    device_id=device_id,
                    token=token,
                    platform=platform,
                    device_info=device_info,
                    is_active=True,
                    last_used=timezone.now()
                )
                created = True
            
            logger.info(f"Token FCM {'créé' if created else 'mis à jour'} pour {user.name} {user.surname}" if hasattr(user, 'name') else f"Client {user.phone_number}")
            return fcm_token
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement du token FCM: {e}")
            raise
    
    @classmethod
    def unregister_token(cls, user: Union[UserDriver, UserCustomer], token: str) -> bool:
        """
        Supprime un token FCM
        """
        try:
            content_type = ContentType.objects.get_for_model(user)
            
            fcm_tokens = FCMToken.objects.filter(
                user_type=content_type,
                user_id=user.id,
                token=token,
                is_active=True
            )
            
            updated_count = fcm_tokens.update(is_active=False)
            
            logger.info(f"Désactivé {updated_count} token(s) FCM pour {user.name} {user.surname}" if hasattr(user, 'name') else f"Client {user.phone_number}")
            return updated_count > 0
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du token FCM: {e}")
            return False
    
    @classmethod
    def get_user_tokens(cls, user: Union[UserDriver, UserCustomer], 
                       active_only: bool = True) -> List[str]:
        """
        Récupère tous les tokens actifs d'un utilisateur
        """
        try:
            content_type = ContentType.objects.get_for_model(user)
            
            tokens_queryset = FCMToken.objects.filter(
                user_type=content_type,
                user_id=user.id
            )
            
            if active_only:
                tokens_queryset = tokens_queryset.filter(is_active=True)
            
            tokens = [fcm_token.token for fcm_token in tokens_queryset]
            
            logger.debug(f"Récupéré {len(tokens)} token(s) pour {user.name} {user.surname}" if hasattr(user, 'name') else f"Client {user.phone_number}")
            return tokens
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des tokens: {e}")
            return []
    
    @classmethod
    def send_notification(cls, 
                         user: Union[UserDriver, UserCustomer],
                         title: str,
                         body: str,
                         data: Optional[Dict] = None,
                         notification_type: str = 'system') -> bool:
        """
        Envoie une notification à un utilisateur spécifique
        """
        try:
            logger.info(f"🔔 Début envoi FCM pour {user.name} {user.surname}" if hasattr(user, 'name') else f"Client {user.phone_number} - Type: {notification_type}")

            # Vérifier si l'utilisateur a une session active
            from applications.authentication.models import Token
            user_type_name = 'driver' if isinstance(user, UserDriver) else 'customer'

            has_active_session = Token.objects.filter(
                user_type=user_type_name,
                user_id=user.id,
                is_active=True
            ).exists()
            
            logger.info(f"🔐 Session active pour {user.name} {user.surname}" if hasattr(user, 'name') else f"Client {user.phone_number}: {'✅ Oui' if has_active_session else '❌ Non'}")
            
            if not has_active_session:
                user_display = f"{user.name} {user.surname}" if hasattr(user, 'name') else f"Client {user.phone_number}"
                logger.info(f"ℹ️  {user_display}: Pas de session active - FCM non envoyée (notification DB créée)")
                return False
            
            tokens = cls.get_user_tokens(user)
            if not tokens:
                logger.warning(f"❌ Aucun token FCM trouvé pour {user.name} {user.surname}" if hasattr(user, 'name') else f"Client {user.phone_number}")
                return False
            
            logger.info(f"✅ {len(tokens)} token(s) FCM trouvé(s) pour {user.name} {user.surname}" if hasattr(user, 'name') else f"Client {user.phone_number}")
            
            result = cls.send_to_tokens(
                tokens=tokens,
                title=title,
                body=body,
                data=data,
                notification_type=notification_type
            )
            
            logger.info(f"🎯 Résultat envoi FCM pour {user.name} {user.surname}" if hasattr(user, 'name') else f"Client {user.phone_number}: {'✅ Succès' if result else '❌ Échec'}")
            return result
            
        except Exception as e:
            logger.error(f"💥 Erreur lors de l'envoi de notification à {user.name} {user.surname}" if hasattr(user, 'name') else f"Client {user.phone_number}: {e}")
            logger.error(traceback.format_exc())
            return False
    
    @classmethod
    def send_to_tokens(cls,
                      tokens: List[str],
                      title: str,
                      body: str,
                      data: Optional[Dict] = None,
                      notification_type: str = 'system') -> bool:
        """
        Envoie une notification à plusieurs tokens en utilisant la nouvelle API Firebase v1
        """
        try:
            logger.info(f"🚀 Début envoi FCM vers {len(tokens)} token(s)")
            logger.info(f"📋 Titre: {title}")
            logger.info(f"💬 Corps: {body[:100]}{'...' if len(body) > 100 else ''}")
            logger.info(f"🏷️ Type: {notification_type}")
            
            # Obtenir le token OAuth2
            oauth2_token = cls.get_firebase_oauth2_token()
            if not oauth2_token:
                logger.error("❌ Échec de l'obtention du token OAuth2")
                return False
            
            logger.info("✅ Token OAuth2 Firebase obtenu")
            
            # Obtenir le project_id depuis le fichier service account
            try:
                with open(settings.FCM_SERVICE_ACCOUNT_PATH, 'r') as f:
                    service_account = json.load(f)
                project_id = service_account['project_id']
                logger.info(f"🔧 Project ID Firebase: {project_id}")
            except Exception as e:
                logger.error(f"❌ Erreur lecture fichier Firebase service account: {e}")
                return False
            
            # Préparer les données
            notification_data = data or {}
            notification_data.update({
                'notification_type': notification_type,
                'timestamp': str(timezone.now().timestamp())
            })
            
            # Convertir toutes les valeurs en string pour FCM
            string_data = {str(k): str(v) for k, v in notification_data.items()}
            
            success_count = 0
            invalid_tokens = []
            
            # Envoyer à chaque token individuellement (nouvelle API Firebase v1)
            for i, token in enumerate(tokens, 1):
                logger.info(f"📤 Envoi {i}/{len(tokens)} vers token: {token[:20]}...")
                
                fcm_message = {
                    "message": {
                        "token": token,
                        "notification": {
                            "title": title,
                            "body": body
                        },
                        "data": string_data,
                        "android": {
                            "notification": {
                                "click_action": "FLUTTER_NOTIFICATION_CLICK",
                                "sound": "default",
                                "channel_id": "woila_notifications"
                            }
                        },
                        "apns": {
                            "payload": {
                                "aps": {
                                    "sound": "default",
                                    "badge": 1,
                                    "content-available": 1
                                }
                            }
                        }
                    }
                }
                
                # Headers avec token OAuth2
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {oauth2_token}"
                }
                
                # Envoyer la requête à l'API FCM v1
                url = cls.FCM_API_URL.format(project_id)
                logger.debug(f"🌐 URL FCM: {url}")
                
                response = requests.post(
                    url,
                    json=fcm_message,
                    headers=headers,
                    timeout=30
                )
                
                logger.info(f"📨 Réponse FCM {i}/{len(tokens)}: Status {response.status_code}")
                
                if response.status_code == 200:
                    success_count += 1
                    logger.info(f"✅ FCM envoyé avec succès au token: {token[:20]}...")
                    response_data = response.json()
                    if 'name' in response_data:
                        logger.debug(f"💌 Message ID Firebase: {response_data['name']}")
                else:
                    logger.error(f"❌ FCM échoué pour token {token[:20]}...: {response.status_code}")
                    logger.error(f"📝 Réponse: {response.text}")
                    # Si le token FCM n'est plus valide, le marquer comme invalide
                    if response.status_code == 404 or "registration token" in response.text.lower():
                        invalid_tokens.append(token)
            
            # Désactiver les tokens invalides
            if invalid_tokens:
                cls._deactivate_invalid_tokens(invalid_tokens)
            
            logger.info(f"FCM envoyé: {success_count}/{len(tokens)} réussis, {len(invalid_tokens)} tokens invalides")
            return success_count > 0
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi FCM: {e}")
            logger.error(traceback.format_exc())
            return False
    
    @classmethod
    def _deactivate_invalid_tokens(cls, invalid_tokens: List[str]):
        """
        Désactive les tokens FCM invalides
        """
        try:
            count = FCMToken.objects.filter(
                token__in=invalid_tokens, 
                is_active=True
            ).update(is_active=False)
            
            logger.info(f"Désactivé {count} token(s) FCM invalide(s)")
                    
        except Exception as e:
            logger.error(f"Erreur lors de la désactivation des tokens: {e}")
    
    @classmethod
    def send_welcome_notification(cls, user: Union[UserDriver, UserCustomer]) -> bool:
        """
        Envoie une notification de bienvenue
        """
        return cls.send_notification(
            user=user,
            title="🎉 Bienvenue sur WOILA !",
            body=f"Bonjour et bienvenue dans la famille WOILA ! Nous sommes ravis de vous compter parmi nous.",
            notification_type='welcome',
            data={
                'welcome_message': True,
                'user_name': user.name if hasattr(user, 'name') else f"Client {user.phone_number}"
            }
        )
    
    @classmethod
    def send_referral_bonus_notification(cls, 
                                       user: Union[UserDriver, UserCustomer],
                                       referral_code: str,
                                       bonus_amount: float) -> bool:
        """
        Envoie une notification de bonus de parrainage
        """
        return cls.send_notification(
            user=user,
            title="🎁 Bonus de parrainage reçu !",
            body=f"Félicitations ! Votre code parrain {referral_code} a été utilisé. Vous avez reçu {bonus_amount} FCFA de bonus !",
            notification_type='referral_used',
            data={
                'referral_code': referral_code,
                'bonus_amount': str(bonus_amount),
                'bonus_type': 'referral'
            }
        )
    
    @classmethod
    def send_vehicle_approval_notification(cls, 
                                         driver: UserDriver,
                                         vehicle_name: str) -> bool:
        """
        Envoie une notification d'approbation de véhicule
        """
        return cls.send_notification(
            user=driver,
            title="🚗✅ Véhicule approuvé !",
            body=f"Excellente nouvelle ! Votre véhicule {vehicle_name} a été approuvé et est maintenant actif sur la plateforme.",
            notification_type='vehicle_approved',
            data={
                'vehicle_name': vehicle_name,
                'approval_status': 'approved'
            }
        )
    
    @classmethod
    def cleanup_inactive_tokens(cls, days_old: int = 30) -> int:
        """
        Nettoie les tokens inactifs plus anciens que X jours
        """
        try:
            cutoff_date = timezone.now() - timezone.timedelta(days=days_old)
            
            count = FCMToken.objects.filter(
                is_active=False,
                updated_at__lt=cutoff_date
            ).delete()[0]
            
            logger.info(f"Supprimé {count} tokens FCM inactifs de plus de {days_old} jours")
            return count
            
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des tokens: {e}")
            return 0
    
    @classmethod
    def get_user_device_count(cls, user: Union[UserDriver, UserCustomer]) -> int:
        """
        Retourne le nombre d'appareils actifs pour un utilisateur
        """
        try:
            content_type = ContentType.objects.get_for_model(user)
            
            return FCMToken.objects.filter(
                user_type=content_type,
                user_id=user.id,
                is_active=True
            ).count()
            
        except Exception as e:
            logger.error(f"Erreur lors du comptage des appareils: {e}")
            return 0
    
    @classmethod
    def send_to_user_type(cls,
                         user_type: str,  # 'driver' ou 'customer'
                         title: str,
                         body: str,
                         data: Optional[Dict] = None,
                         notification_type: str = 'system') -> bool:
        """
        Envoie une notification à tous les utilisateurs d'un type donné
        """
        try:
            if user_type == 'driver':
                model_class = UserDriver
            elif user_type == 'customer':
                model_class = UserCustomer
            else:
                logger.error(f"Type d'utilisateur invalide: {user_type}")
                return False
            
            content_type = ContentType.objects.get_for_model(model_class)
            
            # Récupérer tous les tokens actifs pour ce type d'utilisateur
            tokens = list(FCMToken.objects.filter(
                user_type=content_type,
                is_active=True
            ).values_list('token', flat=True))
            
            if not tokens:
                logger.warning(f"Aucun token FCM actif trouvé pour les {user_type}s")
                return False
            
            logger.info(f"Envoi FCM à {len(tokens)} {user_type}s")
            
            return cls.send_to_tokens(
                tokens=tokens,
                title=title,
                body=body,
                data=data,
                notification_type=notification_type
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi FCM aux {user_type}s: {e}")
            return False