# Configuration admin pour les modèles core uniquement
from django.contrib import admin
from django.utils.html import format_html
from django.db import models
from .models import GeneralConfig, Country, City, VipZone, VipZoneKilometerRule

# Proxy model pour VipZone basé sur la vraie structure de la table
class VipZoneProxy(models.Model):
    name = models.CharField(max_length=100, unique=True)
    prix_jour = models.DecimalField(max_digits=10, decimal_places=2)
    prix_nuit = models.DecimalField(max_digits=10, decimal_places=2)
    active = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    
    class Meta:
        managed = False
        db_table = 'vip_zones'
        verbose_name = "👑 Zone VIP"
        verbose_name_plural = "👑 Zones VIP"

# Proxy model pour VipZoneKilometerRule basé sur la vraie structure de la table
class VipZoneKilometerRuleProxy(models.Model):
    vip_zone = models.ForeignKey(VipZoneProxy, on_delete=models.CASCADE)
    min_kilometers = models.DecimalField(max_digits=5, decimal_places=2)
    prix_jour_per_km = models.DecimalField(max_digits=10, decimal_places=2)
    prix_nuit_per_km = models.DecimalField(max_digits=10, decimal_places=2)
    active = models.BooleanField()
    created_at = models.DateTimeField()
    
    class Meta:
        managed = False
        db_table = 'vip_zone_kilometer_rules'
        verbose_name = "📏 Règle kilométrique VIP"
        verbose_name_plural = "📏 Règles kilométriques VIP"

@admin.register(GeneralConfig)
class GeneralConfigAdmin(admin.ModelAdmin):
    list_display = ['get_config_name', 'search_key', 'get_valeur_preview', 'get_config_type', 'is_active_display', 'updated_at']
    list_filter = ['active', 'created_at', 'updated_at']
    search_fields = ['nom', 'search_key', 'valeur']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 20
    ordering = ['nom']
    
    fieldsets = (
        ('Configuration', {
            'fields': ('nom', 'search_key', 'valeur', 'active'),
            'description': 'Définissez les paramètres de configuration de votre application'
        }),
        ('Informations', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_config_name(self, obj):
        if obj.get_numeric_value() is not None:
            icon = '🔢'
        elif obj.get_boolean_value() is not None:
            icon = '☑️' if obj.get_boolean_value() else '❌'
        else:
            icon = '📝'
        return format_html('{} {}', icon, obj.nom)
    get_config_name.short_description = 'Nom de la configuration'
    
    def get_valeur_preview(self, obj):
        valeur = obj.valeur
        if len(valeur) > 50:
            valeur = valeur[:47] + '...'
        
        numeric_val = obj.get_numeric_value()
        boolean_val = obj.get_boolean_value()
        
        if numeric_val is not None:
            return format_html('<code style="color: white; background: #444; padding: 2px 4px; border-radius: 3px;">{}</code>', valeur)
        elif boolean_val is not None:
            color = '#4CAF50' if boolean_val else '#f44336'
            return format_html('<code style="color: {}; background: #444; padding: 2px 4px; border-radius: 3px;">{}</code>', color, valeur)
        else:
            return format_html('<code style="color: #ddd; background: #444; padding: 2px 4px; border-radius: 3px;">{}</code>', valeur)
    get_valeur_preview.short_description = 'Valeur'
    
    def get_config_type(self, obj):
        if obj.get_numeric_value() is not None:
            return format_html('<span style="color: white; font-weight: bold;">🔢 Numérique</span>')
        elif obj.get_boolean_value() is not None:
            return format_html('<span style="color: #4CAF50; font-weight: bold;">☑️ Booléen</span>')
        else:
            return format_html('<span style="color: #ddd; font-weight: bold;">📝 Texte</span>')
    get_config_type.short_description = 'Type'
    
    def is_active_display(self, obj):
        if obj.active:
            return format_html('<span style="color: green;">✅ Actif</span>')
        else:
            return format_html('<span style="color: red;">❌ Inactif</span>')
    is_active_display.short_description = 'Statut'

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'active', 'created_at']
    list_filter = ['active', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'prix_jour', 'prix_nuit', 'active', 'created_at']
    list_filter = ['active', 'country', 'created_at']
    search_fields = ['name', 'country__name']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['country']

@admin.register(VipZoneProxy)
class VipZoneProxyAdmin(admin.ModelAdmin):
    list_display = ['name_display', 'prix_jour_display', 'prix_nuit_display', 'status_display', 'created_at']
    list_filter = ['active', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    def name_display(self, obj):
        return format_html('👑 {}', obj.name)
    name_display.short_description = 'Zone VIP'
    name_display.admin_order_field = 'name'
    
    def prix_jour_display(self, obj):
        return format_html('☀️ <strong>{} FCFA</strong>', obj.prix_jour)
    prix_jour_display.short_description = 'Prix jour'
    prix_jour_display.admin_order_field = 'prix_jour'
    
    def prix_nuit_display(self, obj):
        return format_html('🌙 <strong>{} FCFA</strong>', obj.prix_nuit)
    prix_nuit_display.short_description = 'Prix nuit'
    prix_nuit_display.admin_order_field = 'prix_nuit'
    
    def status_display(self, obj):
        if obj.active:
            return format_html('<span style="color: green;">✅ Actif</span>')
        else:
            return format_html('<span style="color: red;">❌ Inactif</span>')
    status_display.short_description = 'Statut'
    status_display.admin_order_field = 'active'

@admin.register(VipZoneKilometerRuleProxy)
class VipZoneKilometerRuleProxyAdmin(admin.ModelAdmin):
    list_display = ['zone_display', 'min_km_display', 'prix_jour_km_display', 'prix_nuit_km_display', 'status_display', 'created_at']
    list_filter = ['active', 'vip_zone', 'created_at']
    search_fields = ['vip_zone__name']
    readonly_fields = ['created_at']
    
    def zone_display(self, obj):
        return format_html('👑 {}', obj.vip_zone.name if obj.vip_zone else 'N/A')
    zone_display.short_description = 'Zone VIP'
    zone_display.admin_order_field = 'vip_zone__name'
    
    def min_km_display(self, obj):
        return format_html('📏 À partir de <strong>{} km</strong>', obj.min_kilometers)
    min_km_display.short_description = 'Kilométrage minimum'
    min_km_display.admin_order_field = 'min_kilometers'
    
    def prix_jour_km_display(self, obj):
        return format_html('☀️ <strong>{} FCFA/km</strong>', obj.prix_jour_per_km)
    prix_jour_km_display.short_description = 'Prix/km jour'
    prix_jour_km_display.admin_order_field = 'prix_jour_per_km'
    
    def prix_nuit_km_display(self, obj):
        return format_html('🌙 <strong>{} FCFA/km</strong>', obj.prix_nuit_per_km)
    prix_nuit_km_display.short_description = 'Prix/km nuit'
    prix_nuit_km_display.admin_order_field = 'prix_nuit_per_km'
    
    def status_display(self, obj):
        if obj.active:
            return format_html('<span style="color: green;">✅ Actif</span>')
        else:
            return format_html('<span style="color: red;">❌ Inactif</span>')
    status_display.short_description = 'Statut'
    status_display.admin_order_field = 'active'