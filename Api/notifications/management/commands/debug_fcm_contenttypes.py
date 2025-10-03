"""
Commande pour debugger les ContentTypes des tokens FCM
Usage: python manage.py debug_fcm_contenttypes
"""
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from notifications.models import FCMToken
from users.models import UserDriver, UserCustomer


class Command(BaseCommand):
    help = 'Debug les ContentTypes des tokens FCM'

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS("DEBUG CONTENTTYPES DES TOKENS FCM"))
        self.stdout.write("="*80 + "\n")

        # Afficher les tokens actuels
        tokens = FCMToken.objects.filter(is_active=True)[:5]

        self.stdout.write("[1] Tokens FCM actuels (5 premiers):\n")
        for token in tokens:
            self.stdout.write(f"Token ID: {token.id}")
            self.stdout.write(f"  User ID: {token.user_id}")
            self.stdout.write(f"  ContentType: {token.user_type}")
            self.stdout.write(f"    - app_label: '{token.user_type.app_label}'")
            self.stdout.write(f"    - model: '{token.user_type.model}'")
            self.stdout.write(f"  Platform: {token.platform}\n")

        # Afficher le bon ContentType
        self.stdout.write("\n[2] ContentType CORRECT pour UserDriver:")
        driver_ct = ContentType.objects.get_for_model(UserDriver)
        self.stdout.write(f"  - app_label: '{driver_ct.app_label}'")
        self.stdout.write(f"  - model: '{driver_ct.model}'")
        self.stdout.write(f"  - ID: {driver_ct.id}")

        self.stdout.write("\n[3] ContentType CORRECT pour UserCustomer:")
        customer_ct = ContentType.objects.get_for_model(UserCustomer)
        self.stdout.write(f"  - app_label: '{customer_ct.app_label}'")
        self.stdout.write(f"  - model: '{customer_ct.model}'")
        self.stdout.write(f"  - ID: {customer_ct.id}")

        # Comparer
        self.stdout.write("\n[4] Analyse:")
        wrong_tokens = []
        for token in FCMToken.objects.filter(is_active=True):
            if token.user_type.app_label != 'users':
                wrong_tokens.append(token)

        if wrong_tokens:
            self.stdout.write(self.style.WARNING(
                f"  PROBLEME: {len(wrong_tokens)} token(s) ont un mauvais app_label!"
            ))
            self.stdout.write(f"  Ils ont app_label='{wrong_tokens[0].user_type.app_label}' au lieu de 'users'")
        else:
            self.stdout.write(self.style.SUCCESS(
                "  OK: Tous les tokens ont le bon ContentType"
            ))

        self.stdout.write("\n" + "="*80 + "\n")
