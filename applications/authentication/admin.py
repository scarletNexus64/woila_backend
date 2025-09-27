from django.contrib import admin
from django.utils.html import format_html
from .models import Token, OTPVerification, ReferralCode

@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = ['token_preview', 'user_type_display', 'user_id', 'status_display', 'created_at']
    list_filter = ['user_type', 'is_active', 'created_at']
    search_fields = ['user_id']
    readonly_fields = ['token', 'created_at']
    
    fieldsets = (
        ('👤 Utilisateur', {
            'fields': ('user_type', 'user_id'),
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

# Admin simple basé sur la vraie structure de la table 'otps'
class OTPAdmin(admin.ModelAdmin):
    list_display = ['identifier', 'otp', 'is_verified', 'created_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['identifier']
    readonly_fields = ['created_at']
    
    class Meta:
        verbose_name = "📱 Code OTP"
        verbose_name_plural = "📱 Codes OTP"

# Admin simple basé sur la vraie structure de la table 'referral_codes'  
class ReferralCodeSimpleAdmin(admin.ModelAdmin):
    list_display = ['code', 'user_id', 'user_type', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'user_type']
    search_fields = ['code', 'user_id']
    readonly_fields = ['created_at']
    
    class Meta:
        verbose_name = "🎁 Code de parrainage"
        verbose_name_plural = "🎁 Codes de parrainage"

# Pour contourner le problème des modèles Django vs tables réelles,
# créons des proxies ou utilisons directement les tables via des requêtes raw
from django.db import models

class OTPProxy(models.Model):
    identifier = models.CharField(max_length=100)
    otp = models.CharField(max_length=4)
    created_at = models.DateTimeField()
    is_verified = models.BooleanField()
    
    class Meta:
        managed = False
        db_table = 'otps'
        verbose_name = "📱 Code OTP"
        verbose_name_plural = "📱 Codes OTP"

class ReferralCodeProxy(models.Model):
    user_id = models.IntegerField()
    code = models.CharField(max_length=8)
    created_at = models.DateTimeField()
    is_active = models.BooleanField()
    user_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.CASCADE)
    
    class Meta:
        managed = False
        db_table = 'referral_codes'
        verbose_name = "🎁 Code de parrainage" 
        verbose_name_plural = "🎁 Codes de parrainage"

# Enregistrer les proxies
@admin.register(OTPProxy)
class OTPProxyAdmin(admin.ModelAdmin):
    list_display = ['get_identifier_display', 'get_otp_display', 'get_verified_status', 'created_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['identifier']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('📱 Identifiant', {
            'fields': ('identifier',),
            'description': '📞 Numéro de téléphone ou email'
        }),
        ('🔢 Code OTP', {
            'fields': ('otp',),
            'description': '🔐 Code de vérification à 4 chiffres'
        }),
        ('📊 Statut de vérification', {
            'fields': ('is_verified',),
            'description': '✅ État de validation du code'
        }),
        ('📅 Dates & Historique', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def get_identifier_display(self, obj):
        return format_html('📞 <strong style="color: #1976D2;">{}</strong>', obj.identifier)
    get_identifier_display.short_description = 'Identifiant'
    
    def get_otp_display(self, obj):
        return format_html('🔢 <code style="background: #f5f5f5; padding: 2px 6px; border-radius: 3px; font-weight: bold; font-size: 1.1em;">{}</code>', obj.otp)
    get_otp_display.short_description = 'Code OTP'
    
    def get_verified_status(self, obj):
        if obj.is_verified:
            return format_html('<span style="color: #4CAF50; font-weight: bold;">✅ Vérifié</span>')
        else:
            return format_html('<span style="color: #FF9800; font-weight: bold;">⏳ En attente</span>')
    get_verified_status.short_description = 'Statut'

@admin.register(ReferralCodeProxy)
class ReferralCodeProxyAdmin(admin.ModelAdmin):
    list_display = ['get_code_display', 'get_user_display', 'get_active_status', 'created_at']
    list_filter = ['is_active', 'created_at', 'user_type']
    search_fields = ['code', 'user_id']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('🎁 Code de parrainage', {
            'fields': ('code',),
            'description': '🏷️ Code unique de parrainage'
        }),
        ('👤 Utilisateur', {
            'fields': ('user_id', 'user_type'),
            'description': '🎯 Propriétaire du code de parrainage'
        }),
        ('📊 Statut', {
            'fields': ('is_active',),
            'description': '⚙️ État d\'activation du code'
        }),
        ('📅 Dates & Historique', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def get_code_display(self, obj):
        return format_html('🎁 <strong style="background: #E8F5E8; padding: 3px 8px; border-radius: 5px; color: #2E7D32; font-family: monospace; font-size: 1.1em;">{}</strong>', obj.code)
    get_code_display.short_description = 'Code'
    
    def get_user_display(self, obj):
        return format_html('🚗 <strong>Chauffeur ID {}</strong>', obj.user_id)
    get_user_display.short_description = 'Utilisateur'
    
    def get_active_status(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #4CAF50; font-weight: bold;">🟢 Actif</span>')
        else:
            return format_html('<span style="color: #F44336; font-weight: bold;">🔴 Inactif</span>')
    get_active_status.short_description = 'Statut'