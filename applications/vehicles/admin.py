from django.contrib import admin
from django.utils.html import format_html
from .models import Vehicle, VehicleType, VehicleBrand, VehicleModel, VehicleColor

@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    list_display = ['name_display', 'amount_display', 'status_display']
    list_filter = ['is_active']
    search_fields = ['name']  # ✅ Required for autocomplete
    actions = ['activate', 'deactivate']

    def name_display(self, obj):
        return format_html('🚙 {}', obj.name)
    name_display.short_description = 'Type de véhicule'
    name_display.admin_order_field = 'name'

    def amount_display(self, obj):
        return format_html('💰 {} FCFA', obj.additional_amount)
    amount_display.short_description = 'Montant additionnel'
    amount_display.admin_order_field = 'additional_amount'

    def status_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✅ Actif</span>')
        else:
            return format_html('<span style="color: red;">❌ Inactif</span>')
    status_display.short_description = 'Statut'
    status_display.admin_order_field = 'is_active'
    
    def activate(self, request, queryset):
        queryset.update(is_active=True)
    activate.short_description = "Activer les types sélectionnés"
    
    def deactivate(self, request, queryset):
        queryset.update(is_active=False)
    deactivate.short_description = "Désactiver les types sélectionnés"

@admin.register(VehicleBrand)
class VehicleBrandAdmin(admin.ModelAdmin):
    list_display = ['name_display', 'status_display']
    list_filter = ['is_active']
    search_fields = ['name']  # ✅ Required for autocomplete
    actions = ['activate', 'deactivate']

    def name_display(self, obj):
        return format_html('🏭 {}', obj.name)
    name_display.short_description = 'Marque'
    name_display.admin_order_field = 'name'

    def status_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✅ Actif</span>')
        else:
            return format_html('<span style="color: red;">❌ Inactif</span>')
    status_display.short_description = 'Statut'
    status_display.admin_order_field = 'is_active'
    
    def activate(self, request, queryset):
        queryset.update(is_active=True)
    activate.short_description = "Activer les marques sélectionnées"
    
    def deactivate(self, request, queryset):
        queryset.update(is_active=False)
    deactivate.short_description = "Désactiver les marques sélectionnées"

@admin.register(VehicleModel)
class VehicleModelAdmin(admin.ModelAdmin):
    list_display = ['name_display', 'brand_display', 'status_display']
    list_filter = ['is_active', 'brand']
    search_fields = ['name', 'brand__name']  # ✅ Required for autocomplete
    autocomplete_fields = ['brand']
    actions = ['activate', 'deactivate']

    def name_display(self, obj):
        return format_html('🚗 {}', obj.name)
    name_display.short_description = 'Modèle'
    name_display.admin_order_field = 'name'

    def brand_display(self, obj):
        return format_html('🏭 {}', obj.brand.name if obj.brand else 'N/A')
    brand_display.short_description = 'Marque'
    brand_display.admin_order_field = 'brand__name'

    def status_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✅ Actif</span>')
        else:
            return format_html('<span style="color: red;">❌ Inactif</span>')
    status_display.short_description = 'Statut'
    status_display.admin_order_field = 'is_active'
    
    def activate(self, request, queryset):
        queryset.update(is_active=True)
    activate.short_description = "Activer les modèles sélectionnés"
    
    def deactivate(self, request, queryset):
        queryset.update(is_active=False)
    deactivate.short_description = "Désactiver les modèles sélectionnés"

@admin.register(VehicleColor)
class VehicleColorAdmin(admin.ModelAdmin):
    list_display = ['name_display', 'status_display']
    list_filter = ['is_active']
    search_fields = ['name']  # ✅ Required for autocomplete
    actions = ['activate', 'deactivate']

    def name_display(self, obj):
        return format_html('🎨 {}', obj.name)
    name_display.short_description = 'Couleur'
    name_display.admin_order_field = 'name'

    def status_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✅ Actif</span>')
        else:
            return format_html('<span style="color: red;">❌ Inactif</span>')
    status_display.short_description = 'Statut'
    status_display.admin_order_field = 'is_active'
    
    def activate(self, request, queryset):
        queryset.update(is_active=True)
    activate.short_description = "Activer les couleurs sélectionnées"
    
    def deactivate(self, request, queryset):
        queryset.update(is_active=False)
    deactivate.short_description = "Désactiver les couleurs sélectionnées"

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['plaque_display', 'vehicle_info', 'driver_display', 'etat_display', 'status_display', 'online_status', 'created_at']
    
    def plaque_display(self, obj):
        return format_html('🚗 <strong>{}</strong>', obj.plaque_immatriculation)
    plaque_display.short_description = 'Plaque d\'immatriculation'
    plaque_display.admin_order_field = 'plaque_immatriculation'
    
    def vehicle_info(self, obj):
        return format_html('🏭 {} - 🚗 {} ({})', 
                          obj.brand.name if obj.brand else 'N/A',
                          obj.model.name if obj.model else 'N/A', 
                          obj.nom or 'Pas de nom')
    vehicle_info.short_description = 'Véhicule'
    
    def driver_display(self, obj):
        if obj.driver:
            return format_html('👨‍💼 {} {}', obj.driver.name or '', obj.driver.surname or '')
        return format_html('<span style="color: gray;">❌ Aucun chauffeur</span>')
    driver_display.short_description = 'Chauffeur'
    driver_display.admin_order_field = 'driver__name'
    
    def etat_display(self, obj):
        etat = obj.etat_vehicule
        if etat >= 8:
            color = 'green'
            icon = '✅'
        elif etat >= 6:
            color = 'orange'
            icon = '⚠️'
        else:
            color = 'red'
            icon = '❌'
        return format_html('<span style="color: {};">{} {}/10</span>', color, icon, etat)
    etat_display.short_description = 'État'
    etat_display.admin_order_field = 'etat_vehicule'
    
    def status_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✅ Actif</span>')
        else:
            return format_html('<span style="color: red;">❌ Inactif</span>')
    status_display.short_description = 'Statut'
    status_display.admin_order_field = 'is_active'
    
    def online_status(self, obj):
        if obj.is_online:
            return format_html('<span style="color: green;">🟢 En service</span>')
        else:
            return format_html('<span style="color: red;">🔴 Hors service</span>')
    online_status.short_description = 'Service'
    online_status.admin_order_field = 'is_online'
    list_filter = ['brand', 'model', 'vehicle_type', 'etat_vehicule', 'color', 'is_active', 'is_online', 'created_at']
    search_fields = ['plaque_immatriculation', 'nom', 'brand__name', 'model__name', 'driver__name', 'driver__surname']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 20
    autocomplete_fields = ['driver', 'vehicle_type', 'brand', 'model', 'color']
    
    fieldsets = (
        ('Informations véhicule', {
            'fields': ('driver', 'vehicle_type', 'brand', 'model', 'color', 'nom', 'plaque_immatriculation', 'etat_vehicule')
        }),
        ('Photos extérieures', {
            'fields': ('photo_exterieur_1', 'photo_exterieur_2'),
            'classes': ('collapse',)
        }),
        ('Photos intérieures', {
            'fields': ('photo_interieur_1', 'photo_interieur_2'),
            'classes': ('collapse',)
        }),
        ('État et dates', {
            'fields': ('is_active', 'is_online', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_inactive', 'mark_as_active', 'put_online', 'put_offline']
    
    def mark_as_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} véhicule(s) désactivé(s).')
    mark_as_inactive.short_description = "Désactiver les véhicules sélectionnés"
    
    def mark_as_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} véhicule(s) activé(s).')
    mark_as_active.short_description = "Activer les véhicules sélectionnés"
    
    def put_online(self, request, queryset):
        updated = queryset.update(is_online=True)
        self.message_user(request, f'{updated} véhicule(s) mis en service.')
    put_online.short_description = "Mettre en service"
    
    def put_offline(self, request, queryset):
        updated = queryset.update(is_online=False)
        self.message_user(request, f'{updated} véhicule(s) mis hors service.')
    put_offline.short_description = "Mettre hors service"