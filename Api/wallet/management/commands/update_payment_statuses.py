"""
Commande pour mettre a jour les statuts des transactions en attente
Usage: python manage.py update_payment_statuses
"""
from django.core.management.base import BaseCommand
from wallet.models import WalletTransaction, Wallet
from wallet.services.freemopay import FreemoPayDirect
from django.utils import timezone
from django.db import transaction as db_transaction
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Met a jour les statuts des transactions en attente avec FreeMoPay'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Afficher ce qui serait fait sans modifier la base de donnees',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS("MISE A JOUR DES STATUTS DE PAIEMENT"))
        if dry_run:
            self.stdout.write(self.style.WARNING("MODE DRY-RUN - Aucune modification ne sera faite"))
        self.stdout.write("="*80 + "\n")

        # Recuperer toutes les transactions en processing avec reference FreeMoPay
        processing_transactions = WalletTransaction.objects.filter(
            status='processing'
        ).exclude(
            freemopay_reference__isnull=True
        ).exclude(
            freemopay_reference=''
        ).order_by('created_at')

        self.stdout.write(f"[INFO] {processing_transactions.count()} transaction(s) en processing trouvee(s)\n")

        if processing_transactions.count() == 0:
            self.stdout.write(self.style.SUCCESS("Aucune transaction a mettre a jour!"))
            return

        updated_count = 0
        completed_count = 0
        failed_count = 0
        unchanged_count = 0

        for txn in processing_transactions:
            self.stdout.write(f"\n[{txn.reference}] Verification...")
            self.stdout.write(f"  Type: {txn.transaction_type} | Montant: {txn.amount} FCFA")
            self.stdout.write(f"  FreeMoPay Ref: {txn.freemopay_reference}")
            self.stdout.write(f"  Cree le: {txn.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

            try:
                # Verifier le statut avec FreeMoPay
                freemopay_status = FreemoPayDirect.get_payment_status(txn.freemopay_reference)

                if not freemopay_status:
                    self.stdout.write(self.style.WARNING(
                        f"  WARNING: Impossible de verifier le statut avec FreeMoPay"
                    ))
                    unchanged_count += 1
                    continue

                self.stdout.write(f"  Statut FreeMoPay: {freemopay_status.get('status', 'UNKNOWN')}")

                # Mettre a jour selon le statut
                if freemopay_status.get('status') == 'SUCCESS':
                    self.stdout.write(self.style.SUCCESS("  => SUCCESS - Transaction reussie"))

                    if txn.transaction_type == 'deposit':
                        if not dry_run:
                            with db_transaction.atomic():
                                # Crediter le wallet
                                wallet = Wallet.objects.select_for_update().get(
                                    user_type=txn.user_type,
                                    user_id=txn.user_id
                                )

                                new_balance = wallet.balance + txn.amount
                                wallet.balance = new_balance
                                wallet.save()

                                # Mettre a jour la transaction
                                txn.balance_after = new_balance
                                txn.status = 'completed'
                                txn.completed_at = timezone.now()
                                txn.metadata.update({
                                    'freemopay_check_status': freemopay_status,
                                    'auto_updated_at': timezone.now().isoformat()
                                })
                                txn.save()

                            self.stdout.write(self.style.SUCCESS(
                                f"  Wallet credite: {wallet.balance - txn.amount} -> {wallet.balance} FCFA"
                            ))
                        else:
                            self.stdout.write(
                                f"  [DRY-RUN] Crediterait le wallet de {txn.amount} FCFA"
                            )

                        completed_count += 1
                        updated_count += 1

                    elif txn.transaction_type == 'withdrawal':
                        if not dry_run:
                            txn.status = 'completed'
                            txn.completed_at = timezone.now()
                            txn.metadata.update({
                                'freemopay_check_status': freemopay_status,
                                'auto_updated_at': timezone.now().isoformat()
                            })
                            txn.save()

                        completed_count += 1
                        updated_count += 1

                elif freemopay_status.get('status') in ['FAILED', 'CANCELLED', 'REJECTED']:
                    error_msg = freemopay_status.get('message', 'Transaction echouee')
                    self.stdout.write(self.style.ERROR(
                        f"  => FAILED - {error_msg}"
                    ))

                    if not dry_run:
                        txn.status = 'failed'
                        txn.error_message = error_msg
                        txn.metadata.update({
                            'freemopay_check_status': freemopay_status,
                            'auto_updated_at': timezone.now().isoformat()
                        })
                        txn.save()

                    failed_count += 1
                    updated_count += 1

                elif freemopay_status.get('status') in ['PENDING', 'PROCESSING']:
                    self.stdout.write(self.style.WARNING(
                        "  => PENDING - Toujours en cours chez FreeMoPay"
                    ))
                    unchanged_count += 1

                else:
                    self.stdout.write(self.style.WARNING(
                        f"  => UNKNOWN - Statut inconnu: {freemopay_status.get('status')}"
                    ))
                    unchanged_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"  ERREUR lors de la verification: {str(e)}"
                ))
                logger.error(f"Erreur pour transaction {txn.reference}: {e}", exc_info=True)
                unchanged_count += 1

        # Resume
        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS("RESUME"))
        self.stdout.write("="*80)
        self.stdout.write(f"Total transactions verifiees: {processing_transactions.count()}")
        self.stdout.write(f"Mises a jour: {updated_count}")
        self.stdout.write(f"  - Completees: {completed_count}")
        self.stdout.write(f"  - Echouees: {failed_count}")
        self.stdout.write(f"Inchangees: {unchanged_count}")

        if dry_run:
            self.stdout.write("\n" + self.style.WARNING(
                "MODE DRY-RUN - Aucune modification n'a ete faite"
            ))
            self.stdout.write("Relancez sans --dry-run pour appliquer les modifications")

        self.stdout.write("\n" + "="*80 + "\n")
