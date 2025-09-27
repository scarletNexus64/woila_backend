from django.contrib import admin
from django.utils.html import format_html
from django.db import models
from .models import NotificationConfig, Notification, FCMToken

# Proxy model pour NotificationConfig basé sur la vraie structure de la table
class NotificationConfigProxy(models.Model):
    CHANNEL_CHOICES = [
        ('sms', 'SMS (Nexah)'),
        ('whatsapp', 'WhatsApp (Meta)')
    ]
    
    default_channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    nexah_base_url = models.CharField(max_length=255)
    nexah_send_endpoint = models.CharField(max_length=100)
    nexah_credits_endpoint = models.CharField(max_length=100)
    nexah_user = models.CharField(max_length=100)
    nexah_password = models.CharField(max_length=100)
    nexah_sender_id = models.CharField(max_length=20)
    whatsapp_api_token = models.TextField()
    whatsapp_api_version = models.CharField(max_length=20)
    whatsapp_phone_number_id = models.CharField(max_length=100)
    whatsapp_template_name = models.CharField(max_length=100)
    whatsapp_language = models.CharField(max_length=10)
    updated_at = models.DateTimeField()
    created_at = models.DateTimeField()
    
    def get_default_channel_display(self):
        return dict(self.CHANNEL_CHOICES).get(self.default_channel, self.default_channel)
    
    class Meta:
        managed = False
        db_table = 'notification_configs'
        verbose_name = "⚙️ Configuration de notification"
        verbose_name_plural = "⚙️ Configurations de notification"

# Proxy model pour Notification pour éviter les problèmes avec GenericForeignKey
class NotificationProxy(models.Model):
    NOTIFICATION_TYPES = [
        ('welcome', 'Notification de bienvenue'),
        ('referral_used', 'Code parrain utilisé'),
        ('vehicle_approved', 'Véhicule approuvé'),
        ('system', 'Notification système'),
        ('order', 'Commande'),
        ('other', 'Autre'),
    ]
    
    user_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.CASCADE)
    user_id = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    content = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField()
    read_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    def get_notification_type_display(self):
        return dict(self.NOTIFICATION_TYPES).get(self.notification_type, self.notification_type)
    
    class Meta:
        managed = False
        db_table = 'notifications'
        verbose_name = "🔔 Notification"
        verbose_name_plural = "🔔 Notifications"

@admin.register(NotificationConfigProxy)
class NotificationConfigProxyAdmin(admin.ModelAdmin):
    list_display = ['get_channel_display', 'get_nexah_status', 'get_whatsapp_status', 'is_active_display', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('⚙️ Configuration générale', {
            'fields': ('default_channel',),
            'description': '🎯 Choisissez le canal par défaut pour l\'envoi des codes OTP'
        }),
        ('📱 Configuration SMS (Nexah)', {
            'fields': ('nexah_base_url', 'nexah_send_endpoint', 'nexah_credits_endpoint', 'nexah_user', 'nexah_password', 'nexah_sender_id'),
            'description': '📡 Paramètres pour l\'envoi de SMS via l\'API Nexah',
            'classes': ('collapse',)
        }),
        ('💬 Configuration WhatsApp (Meta)', {
            'fields': ('whatsapp_api_token', 'whatsapp_api_version', 'whatsapp_phone_number_id', 'whatsapp_template_name', 'whatsapp_language'),
            'description': '🟢 Paramètres pour l\'envoi de messages via l\'API WhatsApp de Meta',
            'classes': ('collapse',)
        }),
        ('📅 Dates & Historique', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_channel_display(self, obj):
        if obj.default_channel == 'sms':
            return format_html('📱 <strong style="color: #1976D2;">SMS (Nexah)</strong>')
        elif obj.default_channel == 'whatsapp':
            return format_html('💬 <strong style="color: #25D366;">WhatsApp (Meta)</strong>')
        else:
            return format_html('❓ <strong style="color: #757575;">{}</strong>', obj.get_default_channel_display())
    get_channel_display.short_description = 'Canal par défaut'
    
    def get_nexah_status(self, obj):
        if obj.nexah_user and obj.nexah_password:
            return format_html('<span style="color: #4CAF50; font-weight: bold;">✅ Configuré</span>')
        else:
            return format_html('<span style="color: #F44336; font-weight: bold;">❌ Non configuré</span>')
    get_nexah_status.short_description = 'SMS Nexah'
    
    def get_whatsapp_status(self, obj):
        if obj.whatsapp_api_token and obj.whatsapp_phone_number_id:
            return format_html('<span style="color: #4CAF50; font-weight: bold;">✅ Configuré</span>')
        else:
            return format_html('<span style="color: #F44336; font-weight: bold;">❌ Non configuré</span>')
    get_whatsapp_status.short_description = 'WhatsApp Meta'
    
    def is_active_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #4CAF50; font-weight: bold;">🟢 Actif</span>')
        else:
            return format_html('<span style="color: #F44336; font-weight: bold;">🔴 Inactif</span>')
    is_active_display.short_description = 'Statut'

@admin.register(NotificationProxy)
class NotificationProxyAdmin(admin.ModelAdmin):
    list_display = ['get_title_display', 'get_user_display', 'get_type_display', 'get_read_status', 'get_deleted_status', 'created_at']
    list_filter = ['notification_type', 'is_read', 'is_deleted', 'user_type', 'created_at']
    search_fields = ['title', 'content', 'user_id']
    readonly_fields = ['created_at', 'read_at', 'deleted_at']
    list_per_page = 25
    ordering = ['-created_at']
    actions = ['mark_as_read', 'mark_as_unread', 'soft_delete', 'restore']
    
    fieldsets = (
        ('👤 Destinataire', {
            'fields': ('user_type', 'user_id'),
            'description': '🎯 Utilisateur qui recevra la notification'
        }),
        ('📝 Contenu de la notification', {
            'fields': ('title', 'content', 'notification_type', 'metadata'),
            'description': '✏️ Message et informations de la notification'
        }),
        ('📊 États & Statuts', {
            'fields': ('is_read', 'is_deleted'),
            'description': '📈 États de lecture et suppression'
        }),
        ('📅 Dates & Historique', {
            'fields': ('created_at', 'read_at', 'deleted_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_title_display(self, obj):
        icons = {
            'welcome': '👋',
            'referral_used': '🎁',
            'vehicle_approved': '🚗✅',
            'system': '⚙️',
            'order': '📋',
            'other': '📌'
        }
        icon = icons.get(obj.notification_type, '📌')
        return format_html('{} <strong style="color: #1976D2;">{}</strong>', icon, obj.title)
    get_title_display.short_description = 'Titre'
    
    def get_user_display(self, obj):
        try:
            user_type_name = obj.user_type.model if obj.user_type else 'inconnu'
            user_type_icon = '🚗' if user_type_name == 'userdriver' else '👤'
            return format_html('{} <strong>Utilisateur ID {}</strong> <span style="color: #666; font-size: 0.9em;">({})</span>', user_type_icon, obj.user_id, user_type_name)
        except:
            return format_html('<span style="color: #F44336; font-weight: bold;">❌ Utilisateur ID {} (Type inconnu)</span>', obj.user_id)
    get_user_display.short_description = 'Utilisateur'
    
    def get_type_display(self, obj):
        colors = {
            'welcome': '#4CAF50',
            'referral_used': '#FF9800',
            'vehicle_approved': '#2196F3',
            'system': '#607D8B',
            'order': '#9C27B0',
            'other': '#795548'
        }
        color = colors.get(obj.notification_type, '#666')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_notification_type_display())
    get_type_display.short_description = 'Type'
    
    def get_read_status(self, obj):
        if obj.is_read:
            return format_html('<span style="color: #4CAF50; font-weight: bold;">👁️ Lu</span>')
        else:
            return format_html('<span style="color: #FF9800; font-weight: bold;">📩 Non lu</span>')
    get_read_status.short_description = 'Statut lecture'
    
    def get_deleted_status(self, obj):
        if obj.is_deleted:
            return format_html('<span style="color: #F44336; font-weight: bold;">🗑️ Supprimé</span>')
        else:
            return format_html('<span style="color: #4CAF50; font-weight: bold;">✅ Actif</span>')
    get_deleted_status.short_description = 'Statut suppression'
    
    def mark_as_read(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(is_read=False).update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'👁️ {updated} notification(s) marquée(s) comme lue(s).')
    mark_as_read.short_description = "👁️ Marquer comme lues"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'📩 {updated} notification(s) marquée(s) comme non lue(s).')
    mark_as_unread.short_description = "📩 Marquer comme non lues"
    
    def soft_delete(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(is_deleted=False).update(is_deleted=True, deleted_at=timezone.now())
        self.message_user(request, f'🗑️ {updated} notification(s) supprimée(s).')
    soft_delete.short_description = "🗑️ Supprimer les notifications"
    
    def restore(self, request, queryset):
        updated = queryset.update(is_deleted=False, deleted_at=None)
        self.message_user(request, f'♻️ {updated} notification(s) restaurée(s).')
    restore.short_description = "♻️ Restaurer les notifications"

@admin.register(FCMToken)
class FCMTokenAdmin(admin.ModelAdmin):
    list_display = ['get_user_display', 'get_token_preview', 'platform', 'device_id', 'is_active_display', 'last_used', 'created_at']
    list_filter = ['platform', 'is_active', 'last_used', 'created_at']
    search_fields = ['device_id', 'token', 'user_id']
    readonly_fields = ['created_at', 'updated_at', 'last_used']
    
    fieldsets = (
        ('👤 Utilisateur', {
            'fields': ('user_type', 'user_id'),
            'description': '🎯 Propriétaire du token FCM'
        }),
        ('📱 Token & Appareil', {
            'fields': ('token', 'platform', 'device_id', 'device_info'),
            'description': '🔑 Informations du token et de l\'appareil'
        }),
        ('📊 Statut', {
            'fields': ('is_active',),
            'description': '⚙️ État d\'activation du token'
        }),
        ('📅 Dates & Historique', {
            'fields': ('created_at', 'updated_at', 'last_used'),
            'classes': ['collapse']
        })
    )
    
    actions = ['activate_tokens', 'deactivate_tokens']
    
    def get_user_display(self, obj):
        try:
            if obj.user_type and obj.user:
                user_type = "👤" if obj.user_type.model == 'usercustomer' else "🚗"
                return format_html('{} <strong>{}</strong>', user_type, obj.user)
            elif obj.user_type:
                user_type_name = obj.user_type.model
                user_type = "👤" if user_type_name == 'usercustomer' else "🚗"
                return format_html('{} <strong>Utilisateur ID {}</strong> <span style="color: #666; font-size: 0.9em;">({})</span>', user_type, obj.user_id, user_type_name)
            else:
                return format_html('<span style="color: #F44336; font-weight: bold;">❌ Utilisateur ID {} (Type invalide)</span>', obj.user_id)
        except Exception:
            return format_html('<span style="color: #F44336; font-weight: bold;">❌ Utilisateur ID {} (Erreur de référence)</span>', obj.user_id)
    get_user_display.short_description = 'Utilisateur'
    
    def get_token_preview(self, obj):
        if len(obj.token) > 20:
            return format_html('🔑 <code style="background: #f5f5f5; padding: 2px 4px; border-radius: 3px;">{}...{}</code>', obj.token[:10], obj.token[-10:])
        return format_html('🔑 <code style="background: #f5f5f5; padding: 2px 4px; border-radius: 3px;">{}</code>', obj.token)
    get_token_preview.short_description = 'Token'
    
    def is_active_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #4CAF50; font-weight: bold;">🟢 Actif</span>')
        return format_html('<span style="color: #F44336; font-weight: bold;">🔴 Inactif</span>')
    is_active_display.short_description = 'Statut'
    
    def activate_tokens(self, request, queryset):
        count = queryset.filter(is_active=False).update(is_active=True)
        self.message_user(request, f'✅ {count} token(s) FCM activé(s).')
    activate_tokens.short_description = "✅ Activer les tokens"
    
    def deactivate_tokens(self, request, queryset):
        count = queryset.filter(is_active=True).update(is_active=False)
        self.message_user(request, f'❌ {count} token(s) FCM désactivé(s).')
    deactivate_tokens.short_description = "❌ Désactiver les tokens"