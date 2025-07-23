from django.contrib import admin
from django.utils.html import format_html
from .models import (
    UserDriver, UserCustomer, Token, Document, Vehicle, 
    GeneralConfig, Wallet, ReferralCode,
    VehicleType, VehicleBrand, VehicleModel, VehicleColor
)


@admin.register(GeneralConfig)
class GeneralConfigAdmin(admin.ModelAdmin):
    list_display = [
        'get_config_name', 'search_key', 'get_valeur_preview', 
        'get_config_type', 'is_active_display', 'updated_at'
    ]
    list_filter = ['active', 'created_at', 'updated_at']
    search_fields = ['nom', 'search_key', 'valeur']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 20
    ordering = ['nom']
    
    fieldsets = (
        ('🔧 Configuration', {
            'fields': ('nom', 'search_key', 'valeur', 'active'),
            'description': 'Définissez les paramètres de configuration de votre application'
        }),
        ('📊 Informations', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_config_name(self, obj):
        """Affiche le nom avec une icône selon le type"""
        if obj.get_numeric_value() is not None:
            icon = '🔢'
        elif obj.get_boolean_value() is not None:
            icon = '☑️' if obj.get_boolean_value() else '❌'
        else:
            icon = '📝'
        return format_html(
            '{} {}',
            icon, obj.nom
        )
    get_config_name.short_description = 'Nom de la configuration'
    get_config_name.admin_order_field = 'nom'
    
    def get_valeur_preview(self, obj):
        """Affiche un aperçu de la valeur avec formatage"""
        valeur = obj.valeur
        if len(valeur) > 50:
            valeur = valeur[:47] + '...'
        
        numeric_val = obj.get_numeric_value()
        boolean_val = obj.get_boolean_value()
        
        if numeric_val is not None:
            return format_html(
                '<code style="color: white; background: #444; padding: 2px 4px; border-radius: 3px;">{}</code> <small style="color: #ccc;">(nombre: {})</small>',
                valeur, numeric_val
            )
        elif boolean_val is not None:
            color = '#4CAF50' if boolean_val else '#f4436'  # Vert/Rouge plus visibles
            return format_html(
                '<code style="color: {}; background: #444; padding: 2px 4px; border-radius: 3px;">{}</code> <small style="color: #ccc;">(booléen: {})</small>',
                color, valeur, boolean_val
            )
        else:
            return format_html(
                '<code style="color: #ddd; background: #444; padding: 2px 4px; border-radius: 3px;">{}</code> <small style="color: #ccc;">(texte)</small>',
                valeur
            )
    get_valeur_preview.short_description = 'Valeur'
    
    def get_config_type(self, obj):
        """Détermine et affiche le type de configuration"""
        if obj.get_numeric_value() is not None:
            return format_html('<span style="color: white; font-weight: bold;">🔢 Numérique</span>')
        elif obj.get_boolean_value() is not None:
            return format_html('<span style="color: #4CAF50; font-weight: bold;">☑️ Booléen</span>')
        else:
            return format_html('<span style="color: #ddd; font-weight: bold;">📝 Texte</span>')
    get_config_type.short_description = 'Type'
    
    def is_active_display(self, obj):
        """Affiche le statut actif avec icônes"""
        if obj.active:
            return format_html('<span style="color: green;">✅ Actif</span>')
        else:
            return format_html('<span style="color: red;">❌ Inactif</span>')
    is_active_display.short_description = 'Statut'
    is_active_display.admin_order_field = 'active'
    
    # Actions personnalisées
    actions = ['activate_configs', 'deactivate_configs', 'show_config_examples']
    
    def activate_configs(self, request, queryset):
        """Activer les configurations sélectionnées"""
        updated = queryset.update(active=True)
        self.message_user(request, f'✅ {updated} configuration(s) activée(s).')
    activate_configs.short_description = "✅ Activer les configurations"
    
    def deactivate_configs(self, request, queryset):
        """Désactiver les configurations sélectionnées"""
        updated = queryset.update(active=False)
        self.message_user(request, f'❌ {updated} configuration(s) désactivée(s).')
    deactivate_configs.short_description = "❌ Désactiver les configurations"
    
    def show_config_examples(self, request, queryset):
        """Affiche des exemples de configurations"""
        examples = [
            "💰 DISCOUNT_ORDER_FOR_HOLIDAYS = '20' (réduction de 20%)",
            "🎁 WELCOME_BONUS_AMOUNT = '5000' (bonus de 5000 FCFA)",
            "🚗 MIN_VEHICLE_STATE = '6' (état minimum requis)",
            "✅ ENABLE_REFERRAL_SYSTEM = 'true' (système de parrainage)",
            "📱 MAINTENANCE_MODE = 'false' (mode maintenance)"
        ]
        message = "📋 Exemples de configurations:\n" + "\n".join(examples)
        self.message_user(request, message)
    show_config_examples.short_description = "📋 Voir des exemples"
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('get_user_display', 'get_balance_display', 'get_user_type_display', 'created_at', 'updated_at')
    list_filter = ('user_type', 'created_at')
    search_fields = ('user_id',)
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25
    
    def get_user_display(self, obj):
        return format_html(
            '👤 {}',
            str(obj.user)
        )
    get_user_display.short_description = 'Utilisateur'
    get_user_display.admin_order_field = 'user_id'
    
    def get_balance_display(self, obj):
        color = 'green' if obj.balance > 0 else 'red' if obj.balance < 0 else 'gray'
        return format_html(
            '<span style="color: {}; font-weight: bold;">💰 {} FCFA</span>',
            color, obj.balance
        )
    get_balance_display.short_description = 'Solde'
    get_balance_display.admin_order_field = 'balance'
    
    def get_user_type_display(self, obj):
        icons = {
            'userdriver': '🚗 Chauffeur',
            'usercustomer': '👥 Client'
        }
        user_type_name = obj.user_type.model if obj.user_type else 'Inconnu'
        return format_html(
            '{}',
            icons.get(user_type_name, f'❓ {user_type_name}')
        )
    get_user_type_display.short_description = 'Type'
    get_user_type_display.admin_order_field = 'user_type'

@admin.register(ReferralCode)
class ReferralCodeAdmin(admin.ModelAdmin):
    list_display = ('get_user_display', 'get_code_display', 'get_status_display', 'get_user_type_display', 'created_at')
    list_filter = ('is_active', 'user_type', 'created_at')
    search_fields = ('code', 'user_id')
    readonly_fields = ('created_at',)
    list_per_page = 25
    actions = ['deactivate_codes', 'activate_codes']

    def get_user_display(self, obj):
        return format_html(
            '👤 {}',
            str(obj.user)
        )
    get_user_display.short_description = 'Utilisateur'
    get_user_display.admin_order_field = 'user_id'

    def get_code_display(self, obj):
        return format_html(
            '<code style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px;">🎫 {}</code>',
            obj.code
        )
    get_code_display.short_description = 'Code de parrainage'
    get_code_display.admin_order_field = 'code'

    def get_status_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✅ Actif</span>')
        else:
            return format_html('<span style="color: red;">❌ Inactif</span>')
    get_status_display.short_description = 'Statut'
    get_status_display.admin_order_field = 'is_active'

    def get_user_type_display(self, obj):
        icons = {
            'userdriver': '🚗 Chauffeur',
            'usercustomer': '👥 Client'
        }
        user_type_name = obj.user_type.model if obj.user_type else 'Inconnu'
        return format_html(
            '{}',
            icons.get(user_type_name, f'❓ {user_type_name}')
        )
    get_user_type_display.short_description = 'Type'
    get_user_type_display.admin_order_field = 'user_type'

    def deactivate_codes(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'❌ {updated} code(s) désactivé(s).')
    deactivate_codes.short_description = "❌ Désactiver les codes sélectionnés"

    def activate_codes(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'✅ {updated} code(s) activé(s).')
    activate_codes.short_description = "✅ Activer les codes sélectionnés"


class VehicleInline(admin.TabularInline):
    model = Vehicle
    extra = 0
    fields = ['brand', 'model', 'nom', 'plaque_immatriculation', 'etat_vehicule', 'is_active']
    readonly_fields = ['created_at']
    autocomplete_fields = ['brand', 'model']


@admin.register(UserDriver)
class UserDriverAdmin(admin.ModelAdmin):
    list_display = [
        'get_phone_display', 'get_name_display', 'get_gender_display', 
        'age', 'get_status_display', 'vehicle_count', 'created_at'
    ]
    list_filter = ['gender', 'is_active', 'created_at']
    search_fields = ['phone_number', 'name', 'surname']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 25
    inlines = [VehicleInline]
    
    fieldsets = (
        ('👤 Informations personnelles', {
            'fields': ('phone_number', 'name', 'surname', 'gender', 'age', 'birthday'),
            'description': 'Informations de base du chauffeur'
        }),
        ('🔐 Sécurité', {
            'fields': ('password', 'is_active'),
            'classes': ('collapse',),
            'description': 'Paramètres de sécurité et d\'accès'
        }),
        ('📅 Horodatage', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_phone_display(self, obj):
        return format_html(
            '📱 <strong>{}</strong>',
            obj.phone_number
        )
    get_phone_display.short_description = 'Téléphone'
    get_phone_display.admin_order_field = 'phone_number'
    
    def get_name_display(self, obj):
        return format_html(
            '👨‍💼 {} {}',
            obj.name, obj.surname
        )
    get_name_display.short_description = 'Nom complet'
    get_name_display.admin_order_field = 'name'
    
    def get_gender_display(self, obj):
        icons = {'M': '👨', 'F': '👩', 'O': '⚧️'}
        return format_html(
            '{} {}',
            icons.get(obj.gender, '❓'), obj.get_gender_display()
        )
    get_gender_display.short_description = 'Genre'
    get_gender_display.admin_order_field = 'gender'
    
    def get_status_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✅ Actif</span>')
        else:
            return format_html('<span style="color: red;">❌ Inactif</span>')
    get_status_display.short_description = 'Statut'
    get_status_display.admin_order_field = 'is_active'
    
    def vehicle_count(self, obj):
        count = obj.vehicles.filter(is_active=True).count()
        if count > 0:
            return format_html(
                '<span style="color: green;">🚗 {} véhicule(s)</span>',
                count
            )
        return format_html('<span style="color: gray;">🚫 Aucun véhicule</span>')
    vehicle_count.short_description = 'Véhicules'
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj:
            readonly_fields.append('password')
        return readonly_fields
    
    actions = ['activate_drivers', 'deactivate_drivers']
    
    def activate_drivers(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'✅ {updated} chauffeur(s) activé(s).')
    activate_drivers.short_description = "✅ Activer les chauffeurs"
    
    def deactivate_drivers(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'❌ {updated} chauffeur(s) désactivé(s).')
    deactivate_drivers.short_description = "❌ Désactiver les chauffeurs"

@admin.register(UserCustomer)
class UserCustomerAdmin(admin.ModelAdmin):
    list_display = [
        'get_phone_display', 'get_name_display', 'get_status_display', 
        'get_documents_count', 'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['phone_number', 'name', 'surname']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 25
    
    fieldsets = (
        ('👥 Informations personnelles', {
            'fields': ('phone_number', 'name', 'surname'),
            'description': 'Informations de base du client'
        }),
        ('🔐 Sécurité', {
            'fields': ('password', 'is_active'),
            'classes': ('collapse',),
            'description': 'Paramètres de sécurité et d\'accès'
        }),
        ('📅 Horodatage', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_phone_display(self, obj):
        return format_html(
            '📱 <strong>{}</strong>',
            obj.phone_number
        )
    get_phone_display.short_description = 'Téléphone'
    get_phone_display.admin_order_field = 'phone_number'
    
    def get_name_display(self, obj):
        return format_html(
            '👤 {} {}',
            obj.name, obj.surname
        )
    get_name_display.short_description = 'Nom complet'
    get_name_display.admin_order_field = 'name'
    
    def get_status_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✅ Actif</span>')
        else:
            return format_html('<span style="color: red;">❌ Inactif</span>')
    get_status_display.short_description = 'Statut'
    get_status_display.admin_order_field = 'is_active'
    
    def get_documents_count(self, obj):
        from .models import Document
        count = Document.objects.filter(
            user_type='customer',
            user_id=obj.id,
            is_active=True
        ).count()
        if count > 0:
            return format_html(
                '<span style="color: green;">📄 {} document(s)</span>',
                count
            )
        return format_html('<span style="color: gray;">📄 Aucun document</span>')
    get_documents_count.short_description = 'Documents'
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj:
            readonly_fields.append('password')
        return readonly_fields
    
    actions = ['activate_customers', 'deactivate_customers']
    
    def activate_customers(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'✅ {updated} client(s) activé(s).')
    activate_customers.short_description = "✅ Activer les clients"
    
    def deactivate_customers(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'❌ {updated} client(s) désactivé(s).')
    deactivate_customers.short_description = "❌ Désactiver les clients"

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


@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    list_display = ('get_name_display', 'get_amount_display', 'get_status_display')
    list_filter = ('is_active',)
    search_fields = ('name',)
    actions = ['activate', 'deactivate']

    def get_name_display(self, obj):
        return format_html('🚙 {}', obj.name)
    get_name_display.short_description = 'Type de véhicule'
    get_name_display.admin_order_field = 'name'

    def get_amount_display(self, obj):
        return format_html('💰 {} FCFA', obj.additional_amount)
    get_amount_display.short_description = 'Montant additionnel'
    get_amount_display.admin_order_field = 'additional_amount'

    def get_status_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✅ Actif</span>')
        else:
            return format_html('<span style="color: red;">❌ Inactif</span>')
    get_status_display.short_description = 'Statut'
    get_status_display.admin_order_field = 'is_active'

    def activate(self, request, queryset):
        queryset.update(is_active=True)
    activate.short_description = "✅ Activer les types sélectionnés"

    def deactivate(self, request, queryset):
        queryset.update(is_active=False)
    deactivate.short_description = "❌ Désactiver les types sélectionnés"


@admin.register(VehicleBrand)
class VehicleBrandAdmin(admin.ModelAdmin):
    list_display = ('get_name_display', 'get_status_display')
    list_filter = ('is_active',)
    search_fields = ('name',)
    actions = ['activate', 'deactivate']

    def get_name_display(self, obj):
        return format_html('🏭 {}', obj.name)
    get_name_display.short_description = 'Marque de véhicule'
    get_name_display.admin_order_field = 'name'

    def get_status_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✅ Actif</span>')
        else:
            return format_html('<span style="color: red;">❌ Inactif</span>')
    get_status_display.short_description = 'Statut'
    get_status_display.admin_order_field = 'is_active'

    def activate(self, request, queryset):
        queryset.update(is_active=True)
    activate.short_description = "✅ Activer les marques sélectionnées"

    def deactivate(self, request, queryset):
        queryset.update(is_active=False)
    deactivate.short_description = "❌ Désactiver les marques sélectionnées"


@admin.register(VehicleModel)
class VehicleModelAdmin(admin.ModelAdmin):
    list_display = ('get_name_display', 'get_brand_display', 'get_status_display')
    list_filter = ('is_active', 'brand')
    search_fields = ('name', 'brand__name')
    autocomplete_fields = ['brand']
    actions = ['activate', 'deactivate']

    def get_name_display(self, obj):
        return format_html('🚗 {}', obj.name)
    get_name_display.short_description = 'Modèle de véhicule'
    get_name_display.admin_order_field = 'name'

    def get_brand_display(self, obj):
        return format_html('🏭 {}', obj.brand.name if obj.brand else 'N/A')
    get_brand_display.short_description = 'Marque'
    get_brand_display.admin_order_field = 'brand__name'

    def get_status_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✅ Actif</span>')
        else:
            return format_html('<span style="color: red;">❌ Inactif</span>')
    get_status_display.short_description = 'Statut'
    get_status_display.admin_order_field = 'is_active'

    def activate(self, request, queryset):
        queryset.update(is_active=True)
    activate.short_description = "✅ Activer les modèles sélectionnés"

    def deactivate(self, request, queryset):
        queryset.update(is_active=False)
    deactivate.short_description = "❌ Désactiver les modèles sélectionnés"


@admin.register(VehicleColor)
class VehicleColorAdmin(admin.ModelAdmin):
    list_display = ('get_name_display', 'get_status_display')
    list_filter = ('is_active',)
    search_fields = ('name',)
    actions = ['activate', 'deactivate']

    def get_name_display(self, obj):
        return format_html('🎨 {}', obj.name)
    get_name_display.short_description = 'Couleur de véhicule'
    get_name_display.admin_order_field = 'name'

    def get_status_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✅ Actif</span>')
        else:
            return format_html('<span style="color: red;">❌ Inactif</span>')
    get_status_display.short_description = 'Statut'
    get_status_display.admin_order_field = 'is_active'

    def activate(self, request, queryset):
        queryset.update(is_active=True)
    activate.short_description = "✅ Activer les couleurs sélectionnées"

    def deactivate(self, request, queryset):
        queryset.update(is_active=False)
    deactivate.short_description = "❌ Désactiver les couleurs sélectionnées"


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = [
        'plaque_immatriculation', 'get_vehicle_info', 'get_driver_display', 
        'etat_display', 'color', 'has_images', 'created_at', 'is_active'
    ]
    list_filter = [
        'brand', 'model', 'vehicle_type', 'etat_vehicule', 'color', 'is_active', 'created_at',
        'driver__gender'  # Filtre par genre du chauffeur
    ]
    search_fields = [
        'plaque_immatriculation', 'nom', 
        'brand__name', 'model__name', 'color__name', 'vehicle_type__name',
        'driver__name', 'driver__surname', 'driver__phone_number'
    ]
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 20
    autocomplete_fields = ['driver', 'vehicle_type', 'brand', 'model', 'color']
    
    fieldsets = (
        ('Informations véhicule', {
            'fields': (
                'driver', 'vehicle_type', 'brand', 'model', 'color', 'nom',
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
        return f"{obj.brand} {obj.model} ({obj.nom})"
    get_vehicle_info.short_description = 'Véhicule'
    get_vehicle_info.admin_order_field = 'brand'
    
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
        return super().get_queryset(request).select_related('driver', 'vehicle_type', 'brand', 'model', 'color')
    
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
    
