"""
Commande de gestion Django pour tester le systeme de notifications FCM
Usage: python manage.py test_fcm
"""
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from applications.users.models import UserDriver
from applications.notifications.services.notification_service import NotificationService
from applications.notifications.services.fcm_service import FCMService
from applications.notifications.models import Notification, FCMToken
from applications.authentication.models import Token


class Command(BaseCommand):
    help = 'Test le systeme de notifications FCM'

    def handle(self, *args, **options):
        """Test complet du systeme de notifications"""

        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS("TEST DU SYSTEME DE NOTIFICATIONS WOILA"))
        self.stdout.write("="*80 + "\n")

        # 1. Verifier qu'il y a des drivers enregistres
        self.stdout.write("[1] Verification des drivers...")
        drivers = UserDriver.objects.all()
        self.stdout.write(f"   OK {drivers.count()} driver(s) trouve(s)")

        if drivers.count() == 0:
            self.stdout.write(self.style.ERROR("   ERREUR: Aucun driver trouve pour tester"))
            return

        # Prendre le premier driver avec une session active si possible
        driver = None
        for d in drivers:
            has_session = Token.objects.filter(
                user_type='driver',
                user_id=d.id,
                is_active=True
            ).exists()
            if has_session:
                driver = d
                self.stdout.write(f"   OK Driver trouve avec session active: {d.name} {d.surname} (ID: {d.id})")
                break

        if not driver:
            driver = drivers.first()
            self.stdout.write(self.style.WARNING(
                f"   WARNING: Aucun driver avec session active, utilisation de: {driver.name} {driver.surname} (ID: {driver.id})"
            ))

        # 2. Verifier les notifications en DB
        self.stdout.write("\n[2] Verification des notifications en base de donnees...")
        notifications = Notification.objects.filter(
            user_id=driver.id
        ).order_by('-created_at')[:5]
        self.stdout.write(f"   OK {notifications.count()} notification(s) trouvee(s) pour ce driver")

        for notif in notifications:
            # Encode to ASCII to avoid emoji issues on Windows
            safe_title = notif.title.encode('ascii', 'replace').decode('ascii')
            safe_content = notif.content[:50].encode('ascii', 'replace').decode('ascii')
            self.stdout.write(f"      - [{notif.notification_type}] {safe_title}: {safe_content}...")
            self.stdout.write(
                f"        Creee: {notif.created_at.strftime('%Y-%m-%d %H:%M:%S')} | "
                f"Lue: {'OUI' if notif.is_read else 'NON'}"
            )

        # 3. Verifier les tokens FCM
        self.stdout.write("\n[3] Verification des tokens FCM...")
        driver_content_type = ContentType.objects.get_for_model(UserDriver)
        fcm_tokens = FCMToken.objects.filter(
            user_type=driver_content_type,
            user_id=driver.id,
            is_active=True
        )
        self.stdout.write(f"   OK {fcm_tokens.count()} token(s) FCM actif(s) pour ce driver")

        for token in fcm_tokens:
            self.stdout.write(f"      - Platform: {token.platform} | Device: {token.device_id}")
            self.stdout.write(f"        Token: {token.token[:50]}...")
            self.stdout.write(f"        Cree: {token.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

        # 4. Tester l'envoi d'une notification de test
        self.stdout.write("\n[4] Test d'envoi d'une notification...")

        try:
            # Creer une notification de test
            success = NotificationService.create_notification(
                user=driver,
                title="Test Notification",
                content="Ceci est une notification de test pour verifier le systeme FCM.",
                notification_type="system",
                metadata={
                    "test": True,
                    "timestamp": str(timezone.now())
                }
            )

            if success:
                self.stdout.write(self.style.SUCCESS(
                    "   OK Notification creee en base de donnees avec succes"
                ))

                # Verifier si FCM a ete envoye
                has_session = Token.objects.filter(
                    user_type='driver',
                    user_id=driver.id,
                    is_active=True
                ).exists()

                if has_session:
                    if fcm_tokens.count() > 0:
                        self.stdout.write(self.style.SUCCESS(
                            "   OK Driver a une session active et des tokens FCM"
                        ))
                        self.stdout.write("   INFO: La notification FCM devrait avoir ete envoyee")
                    else:
                        self.stdout.write(self.style.WARNING(
                            "   WARNING: Driver a une session mais aucun token FCM enregistre"
                        ))
                        self.stdout.write(
                            "   INFO: L'app doit s'enregistrer pour recevoir des push notifications"
                        )
                else:
                    self.stdout.write("   INFO: Driver n'a pas de session active")
                    self.stdout.write("   INFO: FCM non envoye (comportement normal)")
            else:
                self.stdout.write(self.style.ERROR("   ERREUR: Echec de la creation de la notification"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ERREUR lors du test d'envoi: {e}"))
            import traceback
            traceback.print_exc()

        # 5. Resume des sessions actives
        self.stdout.write("\n[5] Resume des sessions actives...")
        active_sessions = Token.objects.filter(is_active=True)
        self.stdout.write(f"   OK {active_sessions.count()} session(s) active(s) au total")

        for session in active_sessions[:5]:
            self.stdout.write(f"      - Type: {session.user_type} | User ID: {session.user_id}")
            self.stdout.write(f"        Creee: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS("TEST TERMINE"))
        self.stdout.write("="*80 + "\n")

        # Recommandations
        self.stdout.write("RECOMMANDATIONS:")
        self.stdout.write("   1. Pour recevoir des notifications FCM, le driver doit:")
        self.stdout.write("      - Se connecter a l'app (session active)")
        self.stdout.write("      - Permettre les notifications quand l'app le demande")
        self.stdout.write("      - L'app enregistrera automatiquement le token FCM")
        self.stdout.write("   2. Les notifications sont TOUJOURS sauvegardees en DB")
        self.stdout.write("   3. FCM est envoye seulement si session active + token enregistre")
        self.stdout.write("   4. Verifier les logs Django pour voir les tentatives d'envoi FCM\n")
