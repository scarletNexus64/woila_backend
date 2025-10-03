"""
Commande pour verifier les tokens FCM enregistres
Usage: python manage.py check_fcm_tokens
"""
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from notifications.models import FCMToken
from users.models import UserDriver, UserCustomer


class Command(BaseCommand):
    help = 'Verifie les tokens FCM enregistres dans le systeme'

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS("VERIFICATION DES TOKENS FCM"))
        self.stdout.write("="*80 + "\n")

        # Total tokens
        total_tokens = FCMToken.objects.count()
        active_tokens = FCMToken.objects.filter(is_active=True).count()

        self.stdout.write(f"[1] Statistiques globales:")
        self.stdout.write(f"   Total tokens: {total_tokens}")
        self.stdout.write(f"   Tokens actifs: {active_tokens}")
        self.stdout.write(f"   Tokens inactifs: {total_tokens - active_tokens}")

        # Tokens par type d'utilisateur
        self.stdout.write(f"\n[2] Tokens par type d'utilisateur:")

        driver_ct = ContentType.objects.get_for_model(UserDriver)
        driver_tokens = FCMToken.objects.filter(user_type=driver_ct, is_active=True)
        self.stdout.write(f"   Drivers: {driver_tokens.count()} token(s) actif(s)")

        customer_ct = ContentType.objects.get_for_model(UserCustomer)
        customer_tokens = FCMToken.objects.filter(user_type=customer_ct, is_active=True)
        self.stdout.write(f"   Customers: {customer_tokens.count()} token(s) actif(s)")

        # Tokens par plateforme
        self.stdout.write(f"\n[3] Tokens par plateforme:")
        platforms = FCMToken.objects.filter(is_active=True).values_list('platform', flat=True).distinct()

        for platform in platforms:
            count = FCMToken.objects.filter(platform=platform, is_active=True).count()
            self.stdout.write(f"   {platform}: {count} token(s)")

        # Liste des tokens actifs (derniers 10)
        self.stdout.write(f"\n[4] Derniers tokens actifs:")
        recent_tokens = FCMToken.objects.filter(is_active=True).order_by('-created_at')[:10]

        if recent_tokens.count() == 0:
            self.stdout.write(self.style.WARNING("   Aucun token actif trouve!"))
        else:
            for token in recent_tokens:
                user_type_name = "Driver" if token.user_type.model == "userdriver" else "Customer"
                self.stdout.write(f"   - {user_type_name} #{token.user_id}")
                self.stdout.write(f"     Platform: {token.platform} | Device: {token.device_id}")
                self.stdout.write(f"     Token: {token.token[:30]}...")
                self.stdout.write(f"     Cree: {token.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

        # Verifier le driver 61 specifiquement
        self.stdout.write(f"\n[5] Verification driver ID 61:")
        driver_61_tokens = FCMToken.objects.filter(
            user_type=driver_ct,
            user_id=61
        )

        if driver_61_tokens.count() == 0:
            self.stdout.write(self.style.WARNING("   Aucun token FCM pour driver 61"))
            self.stdout.write("   L'app mobile doit:")
            self.stdout.write("     1. Se connecter avec ce compte")
            self.stdout.write("     2. Accepter les permissions de notifications")
            self.stdout.write("     3. Le token sera automatiquement enregistre")
        else:
            self.stdout.write(f"   {driver_61_tokens.count()} token(s) trouve(s):")
            for token in driver_61_tokens:
                self.stdout.write(f"     - Platform: {token.platform}")
                self.stdout.write(f"       Active: {token.is_active}")
                self.stdout.write(f"       Token: {token.token[:50]}...")
                self.stdout.write(f"       Cree: {token.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS("VERIFICATION TERMINEE"))
        self.stdout.write("="*80 + "\n")
