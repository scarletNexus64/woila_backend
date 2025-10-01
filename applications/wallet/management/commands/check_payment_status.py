"""
Commande pour verifier les statuts de paiement
Usage: python manage.py check_payment_status
"""
from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from applications.wallet.models import WalletTransaction
from decimal import Decimal


class Command(BaseCommand):
    help = 'Verifie les statuts de paiement dans le systeme'

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS("VERIFICATION DES STATUTS DE PAIEMENT"))
        self.stdout.write("="*80 + "\n")

        # 1. Statistiques globales
        self.stdout.write("[1] Statistiques globales:")
        total_transactions = WalletTransaction.objects.count()
        self.stdout.write(f"   Total transactions: {total_transactions}")

        statuts = WalletTransaction.objects.values('status').annotate(
            count=Count('id')
        ).order_by('-count')

        for stat in statuts:
            self.stdout.write(f"   - {stat['status']}: {stat['count']} transaction(s)")

        # 2. Transactions par type
        self.stdout.write("\n[2] Transactions par type:")
        types = WalletTransaction.objects.values('transaction_type').annotate(
            count=Count('id')
        ).order_by('-count')

        for t in types:
            self.stdout.write(f"   - {t['transaction_type']}: {t['count']} transaction(s)")

        # 3. Transactions en attente (pending)
        self.stdout.write("\n[3] Transactions en attente:")
        pending = WalletTransaction.objects.filter(status='pending').order_by('-created_at')[:10]

        if pending.count() == 0:
            self.stdout.write("   Aucune transaction en attente")
        else:
            self.stdout.write(f"   {pending.count()} transaction(s) en attente:")
            for txn in pending:
                self.stdout.write(f"      - Ref: {txn.reference}")
                self.stdout.write(f"        Type: {txn.transaction_type} | Montant: {txn.amount} FCFA")
                self.stdout.write(f"        User: {txn.user_type.model} #{txn.user_id}")
                self.stdout.write(f"        Cree: {txn.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                if txn.freemopay_reference:
                    self.stdout.write(f"        FreeMoPay Ref: {txn.freemopay_reference}")

        # 4. Transactions echouees (failed)
        self.stdout.write("\n[4] Transactions echouees:")
        failed = WalletTransaction.objects.filter(status='failed').order_by('-created_at')[:10]

        if failed.count() == 0:
            self.stdout.write("   Aucune transaction echouee")
        else:
            self.stdout.write(f"   {failed.count()} transaction(s) echouee(s):")
            for txn in failed:
                self.stdout.write(f"      - Ref: {txn.reference}")
                self.stdout.write(f"        Type: {txn.transaction_type} | Montant: {txn.amount} FCFA")
                self.stdout.write(f"        Erreur: {txn.error_message or 'Non specifiee'}")
                self.stdout.write(f"        Cree: {txn.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

        # 5. Transactions completees recentes
        self.stdout.write("\n[5] Dernieres transactions completees:")
        completed = WalletTransaction.objects.filter(status='completed').order_by('-completed_at')[:5]

        total_completed_amount = sum([t.amount for t in completed])

        self.stdout.write(f"   {completed.count()} dernieres transactions completees:")
        for txn in completed:
            self.stdout.write(f"      - Ref: {txn.reference}")
            self.stdout.write(f"        Type: {txn.transaction_type} | Montant: {txn.amount} FCFA")
            self.stdout.write(f"        Description: {txn.description[:50]}...")
            self.stdout.write(f"        Completee: {txn.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")

        # 6. Statistiques financieres
        self.stdout.write("\n[6] Statistiques financieres:")

        deposits_completed = WalletTransaction.objects.filter(
            transaction_type='deposit',
            status='completed'
        ).aggregate(total=Count('id'), amount=Count('amount'))

        withdrawals_completed = WalletTransaction.objects.filter(
            transaction_type='withdrawal',
            status='completed'
        ).aggregate(total=Count('id'), amount=Count('amount'))

        transfers_in = WalletTransaction.objects.filter(
            transaction_type='transfer_in',
            status='completed'
        )

        transfers_out = WalletTransaction.objects.filter(
            transaction_type='transfer_out',
            status='completed'
        )

        total_transfer_in = sum([t.amount for t in transfers_in])
        total_transfer_out = sum([t.amount for t in transfers_out])

        self.stdout.write(f"   Depots completes: {deposits_completed['total']}")
        self.stdout.write(f"   Retraits completes: {withdrawals_completed['total']}")
        self.stdout.write(f"   Transferts entrants: {transfers_in.count()} ({total_transfer_in} FCFA)")
        self.stdout.write(f"   Transferts sortants: {transfers_out.count()} ({total_transfer_out} FCFA)")

        # 7. Transactions avec FreeMoPay
        self.stdout.write("\n[7] Transactions FreeMoPay:")
        with_freemopay = WalletTransaction.objects.exclude(
            Q(freemopay_reference__isnull=True) | Q(freemopay_reference='')
        )

        if with_freemopay.count() == 0:
            self.stdout.write("   Aucune transaction avec reference FreeMoPay")
        else:
            self.stdout.write(f"   {with_freemopay.count()} transaction(s) avec FreeMoPay:")
            for txn in with_freemopay[:10]:
                self.stdout.write(f"      - Ref: {txn.reference}")
                self.stdout.write(f"        FreeMoPay: {txn.freemopay_reference}")
                self.stdout.write(f"        Statut: {txn.status} | Montant: {txn.amount} FCFA")

        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS("VERIFICATION TERMINEE"))
        self.stdout.write("="*80 + "\n")
