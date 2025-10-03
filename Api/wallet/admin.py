from django.contrib import admin
from django.utils.html import format_html
from django.db import models
from .models import Wallet, WalletTransaction

# Proxy model pour éviter les problèmes avec GenericForeignKey
class WalletProxy(models.Model):
    user_id = models.PositiveIntegerField()
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    user_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.CASCADE)
    
    class Meta:
        managed = False
        db_table = 'wallets'
        verbose_name = "💰 Portefeuille"
        verbose_name_plural = "💰 Portefeuilles"

@admin.register(WalletProxy)
class WalletProxyAdmin(admin.ModelAdmin):
    list_display = ['get_user_display', 'get_balance_display', 'get_user_type_display', 'created_at', 'updated_at']
    list_filter = ['user_type', 'created_at']
    search_fields = ['user_id']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 25
    actions = ['delete_all_selected']

    @admin.action(description='🗑️ Supprimer tous les éléments sélectionnés')
    def delete_all_selected(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} portefeuille(s) supprimé(s) avec succès.')

    def get_user_display(self, obj):
        """Affiche le nom complet de l'utilisateur"""
        try:
            # Utiliser le GenericForeignKey pour récupérer l'utilisateur réel
            from users.models import UserDriver, UserCustomer
            if obj.user_type.model == 'userdriver':
                user = UserDriver.objects.filter(id=obj.user_id).first()
            elif obj.user_type.model == 'usercustomer':
                user = UserCustomer.objects.filter(id=obj.user_id).first()
            else:
                user = None

            if user and hasattr(user, 'name') and hasattr(user, 'surname'):
                icon = '🚗' if obj.user_type.model == 'userdriver' else '👤'
                return format_html('{} <strong>{} {}</strong><br><small style="color: #666;">📞 {}</small>',
                                 icon, user.name, user.surname, user.phone_number)
            elif user:
                return format_html('📞 <strong>{}</strong>', user.phone_number)
        except:
            pass
        return format_html('<span style="color: #999;">❌ Utilisateur ID {} ({})</span>',
                         obj.user_id, obj.user_type.model if obj.user_type else 'Inconnu')
    get_user_display.short_description = '👤 Utilisateur'
    get_user_display.admin_order_field = 'user_id'
    
    def get_balance_display(self, obj):
        try:
            balance = float(obj.balance)
            color = 'green' if balance > 0 else 'red' if balance < 0 else 'gray'
            return format_html(
                '<span style="color: {}; font-weight: bold;">💰 {} FCFA</span>',
                color, balance
            )
        except:
            return format_html('<span style="color: gray;">💰 0 FCFA</span>')
    get_balance_display.short_description = 'Solde'
    get_balance_display.admin_order_field = 'balance'
    
    def get_user_type_display(self, obj):
        try:
            icons = {
                'userdriver': '🚗 Chauffeur',
                'usercustomer': '👥 Client'
            }
            user_type_name = obj.user_type.model if obj.user_type else 'Inconnu'
            return format_html(
                '{}',
                icons.get(user_type_name, f'❓ {user_type_name}')
            )
        except:
            return format_html('❓ Type inconnu')
    get_user_type_display.short_description = 'Type'
    get_user_type_display.admin_order_field = 'user_type'


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'reference', 'get_user_display', 'transaction_type_display', 
        'amount_display', 'status_display', 'payment_method', 'created_at'
    ]
    list_filter = [
        'transaction_type', 'status', 'payment_method', 'user_type', 
        'created_at', 'completed_at'
    ]
    search_fields = [
        'reference', 'user_id', 'phone_number', 'freemopay_reference',
        'freemopay_external_id', 'description'
    ]
    readonly_fields = [
        'reference', 'created_at', 'updated_at', 'completed_at',
        'balance_before', 'balance_after'
    ]
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('💰 Transaction', {
            'fields': (
                'reference', 'transaction_type', 'amount', 'status'
            )
        }),
        ('👤 Utilisateur', {
            'fields': ('user_type', 'user_id')
        }),
        ('💳 Paiement', {
            'fields': (
                'payment_method', 'phone_number'
            )
        }),
        ('🏦 FreeMoPay', {
            'fields': (
                'freemopay_reference', 'freemopay_external_id'
            ),
            'classes': ('collapse',)
        }),
        ('📊 Soldes', {
            'fields': (
                'balance_before', 'balance_after'
            )
        }),
        ('📝 Détails', {
            'fields': ('description', 'metadata'),
            'classes': ('collapse',)
        }),
        ('⏰ Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at')
        })
    )
    
    actions = ['mark_as_completed', 'mark_as_failed', 'delete_all_selected']

    @admin.action(description='🗑️ Supprimer tous les éléments sélectionnés')
    def delete_all_selected(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} transaction(s) supprimée(s) avec succès.')

    def get_user_display(self, obj):
        """Affiche le nom complet de l'utilisateur"""
        try:
            # Utiliser le GenericForeignKey pour récupérer l'utilisateur réel
            from users.models import UserDriver, UserCustomer
            if obj.user_type.model == 'userdriver':
                user = UserDriver.objects.filter(id=obj.user_id).first()
            elif obj.user_type.model == 'usercustomer':
                user = UserCustomer.objects.filter(id=obj.user_id).first()
            else:
                user = None

            if user and hasattr(user, 'name') and hasattr(user, 'surname'):
                icon = '🚗' if obj.user_type.model == 'userdriver' else '👤'
                return format_html('{} <strong>{} {}</strong><br><small style="color: #666;">📞 {}</small>',
                                 icon, user.name, user.surname, user.phone_number)
            elif user:
                return format_html('📞 <strong>{}</strong>', user.phone_number)
        except:
            pass
        return format_html('<span style="color: #999;">❌ Utilisateur ID {} ({})</span>',
                         obj.user_id, obj.user_type.model if obj.user_type else 'Inconnu')
    get_user_display.short_description = '👤 Utilisateur'
    get_user_display.admin_order_field = 'user_id'
    
    def transaction_type_display(self, obj):
        icons = {
            'deposit': '💰 Dépôt',
            'withdrawal': '💸 Retrait',
            'transfer_in': '📥 Transfert entrant',
            'transfer_out': '📤 Transfert sortant',
            'refund': '🔄 Remboursement',
            'payment': '💳 Paiement',
        }
        return format_html('{}', icons.get(obj.transaction_type, f'❓ {obj.get_transaction_type_display()}'))
    transaction_type_display.short_description = 'Type'
    transaction_type_display.admin_order_field = 'transaction_type'
    
    def amount_display(self, obj):
        color = 'green' if obj.transaction_type in ['deposit', 'transfer_in', 'refund'] else 'red'
        sign = '+' if obj.transaction_type in ['deposit', 'transfer_in', 'refund'] else '-'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}{} FCFA</span>',
            color, sign, obj.amount
        )
    amount_display.short_description = 'Montant'
    amount_display.admin_order_field = 'amount'
    
    def status_display(self, obj):
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'completed': 'green',
            'failed': 'red',
            'cancelled': 'gray',
        }
        icons = {
            'pending': '⏳',
            'processing': '⚙️',
            'completed': '✅',
            'failed': '❌',
            'cancelled': '🚫',
        }
        color = colors.get(obj.status, 'gray')
        icon = icons.get(obj.status, '❓')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    status_display.short_description = 'Statut'
    status_display.admin_order_field = 'status'
    
    def mark_as_completed(self, request, queryset):
        for transaction in queryset:
            transaction.mark_as_completed()
        self.message_user(request, f"{queryset.count()} transaction(s) marquée(s) comme complétée(s)")
    mark_as_completed.short_description = "Marquer comme complétée"
    
    def mark_as_failed(self, request, queryset):
        for transaction in queryset:
            transaction.mark_as_failed()
        self.message_user(request, f"{queryset.count()} transaction(s) marquée(s) comme échouée(s)")
    mark_as_failed.short_description = "Marquer comme échouée"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user_type')