# Generated manually on 2025-10-03
# This migration reflects the current state of wallet tables

from django.db import migrations, models
import django.db.models.deletion
import wallet.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Wallet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_type', models.ForeignKey(
                    limit_choices_to=models.Q(('app_label', 'users'), ('model', 'userdriver')) | models.Q(('app_label', 'users'), ('model', 'usercustomer')),
                    on_delete=django.db.models.deletion.CASCADE,
                    to='contenttypes.contenttype'
                )),
                ('user_id', models.PositiveIntegerField()),
                ('balance', models.DecimalField(decimal_places=2, default=0.0, max_digits=10, verbose_name='Solde')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Portefeuille',
                'verbose_name_plural': 'Portefeuilles',
                'db_table': 'wallets',
                'unique_together': {('user_type', 'user_id')},
            },
        ),
        migrations.CreateModel(
            name='WalletTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(default=applications.wallet.models.generate_transaction_reference, help_text='Reference unique de la transaction', max_length=50, unique=True, verbose_name='Reference')),
                ('user_type', models.ForeignKey(
                    limit_choices_to=models.Q(('app_label', 'users'), ('model', 'userdriver')) | models.Q(('app_label', 'users'), ('model', 'usercustomer')),
                    on_delete=django.db.models.deletion.CASCADE,
                    to='contenttypes.contenttype'
                )),
                ('user_id', models.PositiveIntegerField()),
                ('transaction_type', models.CharField(choices=[('deposit', 'Depot'), ('withdrawal', 'Retrait'), ('transfer_in', 'Transfert entrant'), ('transfer_out', 'Transfert sortant'), ('refund', 'Remboursement'), ('payment', 'Paiement')], max_length=20, verbose_name='Type de transaction')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Montant')),
                ('status', models.CharField(choices=[('pending', 'En attente'), ('processing', 'En cours'), ('completed', 'Complete'), ('failed', 'Echoue'), ('cancelled', 'Annule')], default='pending', max_length=20, verbose_name='Statut')),
                ('payment_method', models.CharField(blank=True, choices=[('mobile_money', 'Mobile Money'), ('bank_transfer', 'Virement bancaire'), ('cash', 'Especes'), ('other', 'Autre')], max_length=20, verbose_name='Methode de paiement')),
                ('phone_number', models.CharField(blank=True, help_text='Numero pour Mobile Money', max_length=15, verbose_name='Numero de telephone')),
                ('freemopay_reference', models.CharField(blank=True, max_length=100, verbose_name='Reference FreeMoPay')),
                ('freemopay_external_id', models.CharField(blank=True, max_length=100, verbose_name='ID externe FreeMoPay')),
                ('balance_before', models.DecimalField(decimal_places=2, default=0.0, max_digits=10, verbose_name='Solde avant')),
                ('balance_after', models.DecimalField(decimal_places=2, default=0.0, max_digits=10, verbose_name='Solde apres')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('error_message', models.TextField(blank=True, help_text="Message d'erreur en cas d'echec de la transaction", null=True, verbose_name="Message d'erreur")),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='Donnees supplementaires en JSON', verbose_name='Metadonnees')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de creation')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Derniere modification')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='Complete le')),
            ],
            options={
                'verbose_name': 'Transaction Wallet',
                'verbose_name_plural': 'Transactions Wallet',
                'db_table': 'wallet_transactions',
                'ordering': ['-created_at'],
            },
        ),
    ]
