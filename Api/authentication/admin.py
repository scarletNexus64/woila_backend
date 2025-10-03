from django.contrib import admin
from django.utils.html import format_html
from .models import Token, OTPVerification, ReferralCode

@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = ['token_preview', 'get_user_display', 'user_type_display', 'status_display', 'created_at']
    list_filter = ['user_type', 'is_active', 'created_at']
    search_fields = ['user_id']
    readonly_fields = ['token', 'created_at', 'get_user_info']
    actions = ['delete_all_selected']

    @admin.action(description='🗑️ Supprimer tous les éléments sélectionnés')
    def delete_all_selected(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} token(s) supprimé(s) avec succès.')

    fieldsets = (
        ('👤 Utilisateur', {
            'fields': ('get_user_info', 'user_type', 'user_id'),
            'description': '🎯 Informations sur le propriétaire du token'
        }),
        ('🔑 Token d\'authentification', {
            'fields': ('token',),
            'description': '🔐 Token unique généré automatiquement'
        }),
        ('📊 Statut & État', {
            'fields': ('is_active',),
            'description': '⚙️ État d\'activation du token'
        }),
        ('📅 Dates & Historique', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

    def get_user_display(self, obj):
        """Affiche le nom complet de l'utilisateur dans la liste"""
        try:
            user = obj.user
            if user:
                if hasattr(user, 'name') and hasattr(user, 'surname'):
                    return format_html('👤 <strong>{} {}</strong><br><small style="color: #666;">📞 {}</small>',
                                     user.name, user.surname, user.phone_number)
                return format_html('📞 <strong>{}</strong>', user.phone_number)
        except:
            pass
        return format_html('<span style="color: #999;">❌ Utilisateur introuvable (ID: {})</span>', obj.user_id)
    get_user_display.short_description = '👤 Utilisateur'

    def get_user_info(self, obj):
        """Affiche les informations détaillées de l'utilisateur dans le formulaire"""
        try:
            user = obj.user
            if user:
                if hasattr(user, 'name') and hasattr(user, 'surname'):
                    return format_html(
                        '<div style="background: #f5f5f5; padding: 15px; border-radius: 5px;">'
                        '<p><strong>👤 Nom:</strong> {} {}</p>'
                        '<p><strong>📞 Téléphone:</strong> {}</p>'
                        '<p><strong>🆔 ID:</strong> {}</p>'
                        '<p><strong>🏷️ Type:</strong> {}</p>'
                        '</div>',
                        user.name, user.surname, user.phone_number,
                        obj.user_id, 'Chauffeur' if obj.user_type.model == 'userdriver' else 'Client'
                    )
                return format_html(
                    '<div style="background: #f5f5f5; padding: 15px; border-radius: 5px;">'
                    '<p><strong>📞 Téléphone:</strong> {}</p>'
                    '<p><strong>🆔 ID:</strong> {}</p>'
                    '</div>',
                    user.phone_number, obj.user_id
                )
        except:
            pass
        return format_html('<div style="background: #fff3cd; padding: 10px; border-radius: 5px; color: #856404;">⚠️ Utilisateur introuvable (ID: {})</div>', obj.user_id)
    get_user_info.short_description = '📋 Informations utilisateur'
    
    def token_preview(self, obj):
        token_str = str(obj.token)
        if len(token_str) > 20:
            return format_html('🔑 <code style="background: #f5f5f5; padding: 2px 4px; border-radius: 3px; font-family: monospace;">{}...{}</code>', token_str[:8], token_str[-8:])
        return format_html('🔑 <code style="background: #f5f5f5; padding: 2px 4px; border-radius: 3px; font-family: monospace;">{}</code>', token_str)
    token_preview.short_description = 'Token'
    
    def user_type_display(self, obj):
        icons = {'driver': '🚗', 'customer': '👤'}
        colors = {'driver': '#1976D2', 'customer': '#4CAF50'}
        return format_html('{} <strong style="color: {};">{}</strong>', 
                         icons.get(obj.user_type, '❓'), 
                         colors.get(obj.user_type, '#666'),
                         obj.user_type.title())
    user_type_display.short_description = 'Type d\'utilisateur'
    user_type_display.admin_order_field = 'user_type'
    
    def status_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #4CAF50; font-weight: bold;">🟢 Actif</span>')
        else:
            return format_html('<span style="color: #F44336; font-weight: bold;">🔴 Inactif</span>')
    status_display.short_description = 'Statut'
    status_display.admin_order_field = 'is_active'

# Admin pour OTPVerification (table otp_verifications)
@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ['get_phone_display', 'get_otp_display', 'user_type_display', 'get_verified_status', 'get_expiry_status', 'created_at']
    list_filter = ['user_type', 'is_verified', 'created_at']
    search_fields = ['phone_number', 'otp_code']
    readonly_fields = ['created_at', 'expires_at']
    ordering = ['-created_at']
    actions = ['delete_all_selected']

    @admin.action(description='🗑️ Supprimer tous les éléments sélectionnés')
    def delete_all_selected(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} code(s) OTP supprimé(s) avec succès.')

    fieldsets = (
        ('📱 Informations', {
            'fields': ('phone_number', 'user_type'),
            'description': '📞 Numéro de téléphone et type d\'utilisateur'
        }),
        ('🔢 Code OTP', {
            'fields': ('otp_code',),
            'description': '🔐 Code de vérification à 4 chiffres'
        }),
        ('📊 Statut', {
            'fields': ('is_verified', 'attempts'),
            'description': '✅ État de validation et tentatives'
        }),
        ('📅 Dates', {
            'fields': ('created_at', 'expires_at'),
            'classes': ('collapse',)
        })
    )

    def get_phone_display(self, obj):
        return format_html('📞 <strong style="color: #1976D2;">{}</strong>', obj.phone_number)
    get_phone_display.short_description = 'Téléphone'
    get_phone_display.admin_order_field = 'phone_number'

    def get_otp_display(self, obj):
        return format_html('🔢 <code style="background: #FFF3E0; padding: 4px 8px; border-radius: 3px; font-weight: bold; font-size: 1.2em; color: #E65100;">{}</code>', obj.otp_code)
    get_otp_display.short_description = 'Code OTP'

    def user_type_display(self, obj):
        icons = {'driver': '🚗', 'customer': '👤'}
        colors = {'driver': '#1976D2', 'customer': '#4CAF50'}
        return format_html('{} <strong style="color: {};">{}</strong>',
                         icons.get(obj.user_type, '❓'),
                         colors.get(obj.user_type, '#666'),
                         obj.user_type.title())
    user_type_display.short_description = 'Type'
    user_type_display.admin_order_field = 'user_type'

    def get_verified_status(self, obj):
        if obj.is_verified:
            return format_html('<span style="color: #4CAF50; font-weight: bold;">✅ Vérifié</span>')
        else:
            return format_html('<span style="color: #FF9800; font-weight: bold;">⏳ En attente</span>')
    get_verified_status.short_description = 'Vérification'
    get_verified_status.admin_order_field = 'is_verified'

    def get_expiry_status(self, obj):
        if obj.is_expired():
            return format_html('<span style="color: #F44336; font-weight: bold;">❌ Expiré</span>')
        else:
            return format_html('<span style="color: #4CAF50; font-weight: bold;">✅ Valide</span>')
    get_expiry_status.short_description = 'Validité'

# Admin simple basé sur la vraie structure de la table 'referral_codes'  
class ReferralCodeSimpleAdmin(admin.ModelAdmin):
    list_display = ['code', 'user_id', 'user_type', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'user_type']
    search_fields = ['code', 'user_id']
    readonly_fields = ['created_at']
    
    class Meta:
        verbose_name = "🎁 Code de parrainage"
        verbose_name_plural = "🎁 Codes de parrainage"

# Admin pour ReferralCode (table referral_codes)
@admin.register(ReferralCode)
class ReferralCodeAdmin(admin.ModelAdmin):
    list_display = ['get_code_display', 'get_user_display', 'get_active_status', 'used_count', 'created_at']
    list_filter = ['is_active', 'created_at', 'user_type']
    search_fields = ['code', 'user_id']
    readonly_fields = ['created_at', 'used_count']
    ordering = ['-created_at']
    actions = ['delete_all_selected']

    @admin.action(description='🗑️ Supprimer tous les éléments sélectionnés')
    def delete_all_selected(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} code(s) de parrainage supprimé(s) avec succès.')

    fieldsets = (
        ('🎁 Code de parrainage', {
            'fields': ('code',),
            'description': '🏷️ Code unique de parrainage (8 caractères)'
        }),
        ('👤 Utilisateur', {
            'fields': ('user_id', 'user_type'),
            'description': '🎯 Propriétaire du code de parrainage'
        }),
        ('📊 Statut & Utilisation', {
            'fields': ('is_active', 'used_count'),
            'description': '⚙️ État et nombre d\'utilisations'
        }),
        ('📅 Dates', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

    def get_code_display(self, obj):
        return format_html('🎁 <strong style="background: #E8F5E8; padding: 3px 8px; border-radius: 5px; color: #2E7D32; font-family: monospace; font-size: 1.1em;">{}</strong>', obj.code)
    get_code_display.short_description = 'Code'
    get_code_display.admin_order_field = 'code'

    def get_user_display(self, obj):
        """Affiche le nom complet de l'utilisateur"""
        try:
            user = obj.user
            if user:
                if hasattr(user, 'name') and hasattr(user, 'surname'):
                    icon = '🚗' if obj.user_type.model == 'userdriver' else '👤'
                    return format_html('{} <strong>{} {}</strong><br><small style="color: #666;">📞 {}</small>',
                                     icon, user.name, user.surname, user.phone_number)
                return format_html('📞 <strong>{}</strong>', user.phone_number)
        except:
            pass
        return format_html('<span style="color: #999;">❌ Utilisateur ID {} ({})</span>',
                         obj.user_id, obj.user_type.model if obj.user_type else 'Inconnu')
    get_user_display.short_description = '👤 Utilisateur'

    def get_active_status(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #4CAF50; font-weight: bold;">🟢 Actif</span>')
        else:
            return format_html('<span style="color: #F44336; font-weight: bold;">🔴 Inactif</span>')
    get_active_status.short_description = 'Statut'
    get_active_status.admin_order_field = 'is_active'