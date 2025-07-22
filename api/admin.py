from django.contrib import admin
from .models import UserDriver, UserCustomer, Token, Document

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
