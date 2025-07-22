from django.contrib import admin
from django.utils.html import format_html
from .models import UserDriver, UserCustomer, Token, Document, Vehicle

@admin.register(UserDriver)
class UserDriverAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'name', 'surname', 'gender', 'age', 'is_active', 'created_at']
    list_filter = ['gender', 'is_active', 'created_at']
    search_fields = ['phone_number', 'name', 'surname']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('phone_number', 'name', 'surname', 'gender', 'age', 'birthday')
        }),
        ('Sécurité', {
            'fields': ('password', 'is_active'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj:  # Si on modifie un objet existant
            readonly_fields.append('password')
        return readonly_fields

@admin.register(UserCustomer)
class UserCustomerAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'name', 'surname', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['phone_number', 'name', 'surname']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('phone_number', 'name', 'surname')
        }),
        ('Sécurité', {
            'fields': ('password', 'is_active'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj:  # Si on modifie un objet existant
            readonly_fields.append('password')
        return readonly_fields

@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = ['token', 'user_type', 'user_id', 'is_active', 'created_at']
    list_filter = ['user_type', 'is_active', 'created_at']
    search_fields = ['token', 'user_id']
    readonly_fields = ['token', 'created_at']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['document_name', 'get_user_display', 'user_type', 'original_filename', 'file_size_display', 'uploaded_at', 'is_active']
    list_filter = ['user_type', 'document_name', 'is_active', 'uploaded_at', 'content_type']
    search_fields = ['document_name', 'original_filename', 'user_id']
    readonly_fields = ['original_filename', 'file_size', 'content_type', 'uploaded_at']
    list_per_page = 20
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user_id', 'user_type')
        }),
        ('Document', {
            'fields': ('document_name', 'file', 'is_active')
        }),
        ('Informations du fichier', {
            'fields': ('original_filename', 'file_size', 'content_type'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_user_display(self, obj):
        """Affiche les infos de l'utilisateur dans la liste"""
        return obj.get_user_info()
    get_user_display.short_description = 'Utilisateur'
    get_user_display.admin_order_field = 'user_id'
    
    def file_size_display(self, obj):
        """Affiche la taille du fichier en format lisible"""
        if obj.file_size:
            if obj.file_size < 1024:
                return f"{obj.file_size} B"
            elif obj.file_size < 1024 * 1024:
                return f"{obj.file_size / 1024:.1f} KB"
            else:
                return f"{obj.file_size / (1024 * 1024):.1f} MB"
        return "-"
    file_size_display.short_description = 'Taille'
    file_size_display.admin_order_field = 'file_size'
    
    def get_queryset(self, request):
        """Optimise les requêtes pour éviter le problème N+1"""
        return super().get_queryset(request).select_related()
    
    # Actions personnalisées
    actions = ['mark_as_inactive', 'mark_as_active']
    
    def mark_as_inactive(self, request, queryset):
        """Désactiver les documents sélectionnés"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} document(s) désactivé(s).')
    mark_as_inactive.short_description = "Désactiver les documents sélectionnés"
    
    def mark_as_active(self, request, queryset):
        """Activer les documents sélectionnés"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} document(s) activé(s).')
    mark_as_active.short_description = "Activer les documents sélectionnés"


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = [
        'plaque_immatriculation', 'get_vehicle_info', 'get_driver_display', 
        'etat_display', 'couleur', 'has_images', 'created_at', 'is_active'
    ]
    list_filter = [
        'marque', 'etat_vehicule', 'couleur', 'is_active', 'created_at',
        'driver__gender'  # Filtre par genre du chauffeur
    ]
    search_fields = [
        'plaque_immatriculation', 'marque', 'nom', 'modele', 
        'driver__name', 'driver__surname', 'driver__phone_number'
    ]
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 20
    
    fieldsets = (
        ('Informations véhicule', {
            'fields': (
                'driver', 'marque', 'nom', 'modele', 'couleur', 
                'plaque_immatriculation', 'etat_vehicule'
            )
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
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_vehicle_info(self, obj):
        """Affiche les infos du véhicule"""
        return f"{obj.marque} {obj.nom} ({obj.modele})"
    get_vehicle_info.short_description = 'Véhicule'
    get_vehicle_info.admin_order_field = 'marque'
    
    def get_driver_display(self, obj):
        """Affiche les infos du chauffeur"""
        return obj.get_driver_info()
    get_driver_display.short_description = 'Chauffeur'
    get_driver_display.admin_order_field = 'driver__name'
    
    def etat_display(self, obj):
        """Affiche l'état avec indicateur visuel"""
        etat = obj.etat_vehicule
        if etat >= 8:
            color = 'green'
            icon = '✓'
        elif etat >= 6:
            color = 'orange'
            icon = '!'
        else:
            color = 'red'
            icon = '✗'
        
        return format_html(
            '<span style="color: {};">{} {}/10</span>',
            color, icon, etat
        )
    etat_display.short_description = 'État'
    etat_display.admin_order_field = 'etat_vehicule'
    
    def has_images(self, obj):
        """Indique si le véhicule a des photos"""
        images = [obj.photo_exterieur_1, obj.photo_exterieur_2, obj.photo_interieur_1, obj.photo_interieur_2]
        count = sum(1 for img in images if img)
        
        if count == 4:
            return format_html(
                '<span style="color: green;">✓ {}/4</span>',
                count
            )
        elif count >= 2:
            return format_html(
                '<span style="color: orange;">! {}/4</span>',
                count
            )
        else:
            return format_html(
                '<span style="color: red;">✗ {}/4</span>',
                count
            )
    has_images.short_description = 'Photos'
    
    def get_queryset(self, request):
        """Optimise les requêtes"""
        return super().get_queryset(request).select_related('driver')
    
    # Actions personnalisées
    actions = ['mark_as_inactive', 'mark_as_active', 'reset_vehicle_state']
    
    def mark_as_inactive(self, request, queryset):
        """Désactiver les véhicules sélectionnés"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} véhicule(s) désactivé(s).')
    mark_as_inactive.short_description = "Désactiver les véhicules sélectionnés"
    
    def mark_as_active(self, request, queryset):
        """Activer les véhicules sélectionnés"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} véhicule(s) activé(s).')
    mark_as_active.short_description = "Activer les véhicules sélectionnés"
    
    def reset_vehicle_state(self, request, queryset):
        """Remettre l'état à 7/10 pour les véhicules sélectionnés"""
        updated = queryset.update(etat_vehicule=7)
        self.message_user(request, f'{updated} véhicule(s) remis à l\'état 7/10.')
    reset_vehicle_state.short_description = "Remettre l'état à 7/10"
    
    # Inline pour voir les véhicules depuis la page chauffeur
    class VehicleInline(admin.TabularInline):
        model = Vehicle
        extra = 0
        fields = ['marque', 'nom', 'plaque_immatriculation', 'etat_vehicule', 'is_active']
        readonly_fields = ['created_at']


# Ajouter l'inline aux chauffeurs
class UserDriverAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'name', 'surname', 'gender', 'age', 'vehicle_count', 'is_active', 'created_at']
    list_filter = ['gender', 'is_active', 'created_at']
    search_fields = ['phone_number', 'name', 'surname']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [VehicleAdmin.VehicleInline]
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('phone_number', 'name', 'surname', 'gender', 'age', 'birthday')
        }),
        ('Sécurité', {
            'fields': ('password', 'is_active'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj:  # Si on modifie un objet existant
            readonly_fields.append('password')
        return readonly_fields
    
    def vehicle_count(self, obj):
        """Nombre de véhicules du chauffeur"""
        count = obj.vehicles.filter(is_active=True).count()
        if count > 0:
            return format_html(
                '<span style="color: green;">{} véhicule(s)</span>',
                count
            )
        return format_html(
            '<span style="color: gray;">0 véhicule</span>'
        )
    vehicle_count.short_description = 'Véhicules'


# Re-register UserDriver with the updated admin
admin.site.unregister(UserDriver)
admin.site.register(UserDriver, UserDriverAdmin)
