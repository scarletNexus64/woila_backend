from django.contrib import admin
from django.utils.html import format_html
from .models import UserDriver, UserCustomer, Document

@admin.register(UserDriver)
class UserDriverAdmin(admin.ModelAdmin):
    list_display = ['phone_display', 'name_display', 'gender_display', 'age', 'status_display', 'created_at']
    list_filter = ['gender', 'is_active', 'is_partenaire_interne', 'is_partenaire_externe', 'created_at']
    search_fields = ['phone_number', 'name', 'surname']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['delete_all_selected']

    @admin.action(description='🗑️ Supprimer tous les éléments sélectionnés')
    def delete_all_selected(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} chauffeur(s) supprimé(s) avec succès.')

    def phone_display(self, obj):
        return format_html('📱 {}', obj.phone_number)
    phone_display.short_description = '🚗 Téléphone Chauffeur'
    phone_display.admin_order_field = 'phone_number'
    
    def name_display(self, obj):
        return format_html('👨‍💼 {} {}', obj.name or '', obj.surname or '')
    name_display.short_description = 'Nom complet'
    name_display.admin_order_field = 'name'
    
    def gender_display(self, obj):
        icons = {'M': '👨', 'F': '👩', 'O': '⚧️'}
        return format_html('{} {}', icons.get(obj.gender, '❓'), obj.get_gender_display() if hasattr(obj, 'get_gender_display') else obj.gender)
    gender_display.short_description = 'Genre'
    gender_display.admin_order_field = 'gender'
    
    def status_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✅ Actif</span>')
        else:
            return format_html('<span style="color: red;">❌ Inactif</span>')
    status_display.short_description = 'Statut'
    status_display.admin_order_field = 'is_active'
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('phone_number', 'name', 'surname', 'gender', 'age', 'birthday', 'profile_picture')
        }),
        ('Type de partenariat', {
            'fields': ('is_partenaire_interne', 'is_partenaire_externe')
        }),
        ('Statut et sécurité', {
            'fields': ('password', 'is_active')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(UserCustomer)
class UserCustomerAdmin(admin.ModelAdmin):
    list_display = ['phone_display', 'name_display', 'status_display', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['phone_number', 'name', 'surname']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['delete_all_selected']

    @admin.action(description='🗑️ Supprimer tous les éléments sélectionnés')
    def delete_all_selected(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} client(s) supprimé(s) avec succès.')

    def phone_display(self, obj):
        return format_html('📱 {}', obj.phone_number)
    phone_display.short_description = '👥 Téléphone Client'
    phone_display.admin_order_field = 'phone_number'

    def name_display(self, obj):
        name = obj.name or ''
        surname = obj.surname or ''
        full_name = f'{name} {surname}'.strip()
        if full_name:
            return format_html('👤 {}', full_name)
        else:
            return format_html('<span style="color: gray;">Non renseigné</span>')
    name_display.short_description = 'Nom complet'
    name_display.admin_order_field = 'name'

    def status_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✅ Actif</span>')
        else:
            return format_html('<span style="color: red;">❌ Inactif</span>')
    status_display.short_description = 'Statut'
    status_display.admin_order_field = 'is_active'

    fieldsets = (
        ('Informations personnelles', {
            'fields': ('phone_number', 'name', 'surname')
        }),
        ('Statut et sécurité', {
            'fields': ('password', 'is_active')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['document_name', 'user_type', 'user_id', 'original_filename', 'is_active', 'uploaded_at']
    list_filter = ['user_type', 'document_name', 'is_active', 'uploaded_at']
    search_fields = ['document_name', 'original_filename', 'user_id']
    readonly_fields = ['original_filename', 'file_size', 'content_type', 'uploaded_at']
    actions = ['delete_all_selected']

    @admin.action(description='🗑️ Supprimer tous les éléments sélectionnés')
    def delete_all_selected(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} document(s) supprimé(s) avec succès.')

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
        ('Dates', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        })
    )