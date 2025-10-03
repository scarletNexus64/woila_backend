"""
Commande pour migrer les ContentTypes des tokens FCM de 'api' vers 'users'
Usage: python manage.py migrate_fcm_contenttypes
"""
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from notifications.models import FCMToken
from users.models import UserDriver, UserCustomer


class Command(BaseCommand):
    help = 'Migre les ContentTypes des tokens FCM de app_label=api vers app_label=users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Afficher ce qui serait fait sans modifier la base de donnees',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS("MIGRATION DES CONTENTTYPES FCM"))
        if dry_run:
            self.stdout.write(self.style.WARNING("MODE DRY-RUN - Aucune modification ne sera faite"))
        self.stdout.write("="*80 + "\n")

        # Obtenir les bons ContentTypes
        correct_driver_ct = ContentType.objects.get_for_model(UserDriver)
        correct_customer_ct = ContentType.objects.get_for_model(UserCustomer)

        self.stdout.write(f"ContentTypes corrects:")
        self.stdout.write(f"  Driver: app_label='{correct_driver_ct.app_label}', model='{correct_driver_ct.model}'")
        self.stdout.write(f"  Customer: app_label='{correct_customer_ct.app_label}', model='{correct_customer_ct.model}'")

        # Trouver les anciens ContentTypes (app_label='api')
        try:
            old_driver_ct = ContentType.objects.get(app_label='api', model='userdriver')
            old_customer_ct = ContentType.objects.get(app_label='api', model='usercustomer')
        except ContentType.DoesNotExist:
            self.stdout.write(self.style.SUCCESS("\nAucun ancien ContentType trouve - Migration deja effectuee!"))
            return

        # Compter les tokens a migrer
        driver_tokens = FCMToken.objects.filter(user_type=old_driver_ct)
        customer_tokens = FCMToken.objects.filter(user_type=old_customer_ct)

        total = driver_tokens.count() + customer_tokens.count()

        self.stdout.write(f"\nTokens a migrer:")
        self.stdout.write(f"  Drivers: {driver_tokens.count()} token(s)")
        self.stdout.write(f"  Customers: {customer_tokens.count()} token(s)")
        self.stdout.write(f"  TOTAL: {total} token(s)")

        if total == 0:
            self.stdout.write(self.style.SUCCESS("\nAucun token a migrer!"))
            return

        # Migrer
        if not dry_run:
            self.stdout.write("\nMigration en cours...")

            # Migrer les drivers
            updated_drivers = driver_tokens.update(user_type=correct_driver_ct)
            self.stdout.write(f"  Drivers: {updated_drivers} token(s) migre(s)")

            # Migrer les customers
            updated_customers = customer_tokens.update(user_type=correct_customer_ct)
            self.stdout.write(f"  Customers: {updated_customers} token(s) migre(s)")

            self.stdout.write(self.style.SUCCESS(f"\nMigration terminee! {updated_drivers + updated_customers} token(s) mis a jour"))
        else:
            self.stdout.write("\n[DRY-RUN] Migration qui serait effectuee:")
            self.stdout.write(f"  {driver_tokens.count()} driver token(s): api.userdriver -> users.userdriver")
            self.stdout.write(f"  {customer_tokens.count()} customer token(s): api.usercustomer -> users.usercustomer")

        # Verification
        self.stdout.write("\nVerification post-migration:")
        wrong_tokens = FCMToken.objects.exclude(
            user_type__app_label='users'
        ).count()

        if wrong_tokens == 0:
            self.stdout.write(self.style.SUCCESS("  OK: Tous les tokens ont maintenant le bon ContentType!"))
        else:
            self.stdout.write(self.style.WARNING(
                f"  ATTENTION: {wrong_tokens} token(s) ont encore un mauvais ContentType"
            ))

        self.stdout.write("\n" + "="*80 + "\n")
