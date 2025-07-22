from django.contrib import admin
from .models import UserDriver, UserCustomer, Token

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
