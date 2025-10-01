"""
Commande pour tester l'envoi de push notifications FCM
Usage: python manage.py test_push_notification --user-id=61 --user-type=driver
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from applications.users.models import UserDriver, UserCustomer
from applications.notifications.services.notification_service import NotificationService


class Command(BaseCommand):
    help = 'Teste l envoi de push notifications FCM'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            required=True,
            help='ID de l utilisateur'
        )
        parser.add_argument(
            '--user-type',
            type=str,
            required=True,
            choices=['driver', 'customer'],
            help='Type d utilisateur (driver ou customer)'
        )

    def handle(self, *args, **options):
        user_id = options['user_id']
        user_type = options['user_type']

        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS("TEST DE PUSH NOTIFICATION FCM"))
        self.stdout.write("="*80 + "\n")

        # Recuperer l'utilisateur
        try:
            if user_type == 'driver':
                user = UserDriver.objects.get(id=user_id)
                user_display = f"Driver {user.name} {user.surname} (ID: {user.id})"
            else:
                user = UserCustomer.objects.get(id=user_id)
                user_display = f"Customer ID: {user.id}"
        except (UserDriver.DoesNotExist, UserCustomer.DoesNotExist):
            self.stdout.write(self.style.ERROR(
                f"Erreur: {user_type} avec ID {user_id} introuvable"
            ))
            return

        self.stdout.write(f"Utilisateur: {user_display}\n")

        # Envoyer la notification de test
        try:
            self.stdout.write("Envoi de la notification de test...")

            notification = NotificationService.create_notification(
                user=user,
                title="Test Push Notification",
                content="Ceci est une notification de test pour verifier que les push FCM fonctionnent correctement. Si vous recevez ce message, le systeme fonctionne parfaitement!",
                notification_type="system",
                metadata={
                    "test": True,
                    "timestamp": str(timezone.now())
                }
            )

            if notification:
                self.stdout.write(self.style.SUCCESS(
                    f"\nOK: Notification creee avec succes (ID: {notification.id})"
                ))
                self.stdout.write(f"  Titre: {notification.title}")
                self.stdout.write(f"  Type: {notification.notification_type}")
                self.stdout.write(f"  Date: {notification.created_at}")

                # Verifier si l'utilisateur a des tokens FCM
                from applications.notifications.models import FCMToken
                from django.contrib.contenttypes.models import ContentType

                ct = ContentType.objects.get_for_model(user)
                tokens = FCMToken.objects.filter(
                    user_type=ct,
                    user_id=user.id,
                    is_active=True
                )

                self.stdout.write(f"\nTokens FCM: {tokens.count()} token(s) actif(s)")

                if tokens.count() > 0:
                    self.stdout.write(self.style.SUCCESS(
                        "  => Push notification devrait etre envoyee!"
                    ))
                    for token in tokens:
                        self.stdout.write(f"     - Platform: {token.platform}")
                        self.stdout.write(f"       Token: {token.token[:50]}...")
                else:
                    self.stdout.write(self.style.WARNING(
                        "  => Aucun token FCM - Push notification NON envoyee"
                    ))
                    self.stdout.write("     L'utilisateur doit se connecter et autoriser les notifications")

                # Verifier la session
                from applications.authentication.models import Token
                has_session = Token.objects.filter(
                    user_type=user_type,
                    user_id=user.id,
                    is_active=True
                ).exists()

                self.stdout.write(f"\nSession active: {'OUI' if has_session else 'NON'}")

            else:
                self.stdout.write(self.style.ERROR(
                    "ERREUR: Impossible de creer la notification"
                ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nErreur: {str(e)}"))
            import traceback
            traceback.print_exc()

        self.stdout.write("\n" + "="*80 + "\n")
