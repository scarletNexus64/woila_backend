from rest_framework import serializers
from .models import Notification, FCMToken, NotificationConfig


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer pour les notifications"""
    time_ago = serializers.SerializerMethodField()
    user_info = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'user_type', 'user_id', 'user_info',
            'title', 'content', 'notification_type',
            'is_read', 'is_deleted', 'metadata',
            'created_at', 'read_at', 'deleted_at', 'time_ago'
        ]
        read_only_fields = [
            'id', 'created_at', 'read_at', 'deleted_at',
            'time_ago', 'user_info'
        ]

    def get_time_ago(self, obj):
        from django.utils.timesince import timesince
        return timesince(obj.created_at)

    def get_user_info(self, obj):
        return f"{obj.user_type.model} {obj.user_id}"


class NotificationListSerializer(serializers.ModelSerializer):
    """Serializer simple pour la liste des notifications"""
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'content', 'notification_type',
            'is_read', 'created_at', 'time_ago'
        ]
        read_only_fields = ['id', 'created_at', 'time_ago']

    def get_time_ago(self, obj):
        from django.utils.timesince import timesince
        return timesince(obj.created_at)


class FCMTokenRegisterSerializer(serializers.ModelSerializer):
    """Serializer pour enregistrer un token FCM"""
    
    class Meta:
        model = FCMToken
        fields = ['token', 'platform', 'device_id', 'device_info']


class FCMTokenSerializer(serializers.ModelSerializer):
    """Serializer pour les tokens FCM"""
    token_preview = serializers.SerializerMethodField()

    class Meta:
        model = FCMToken
        fields = [
            'id', 'user_type', 'user_id', 'token', 'token_preview',
            'platform', 'device_id', 'device_info',
            'is_active', 'last_used', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'last_used', 'token_preview'
        ]

    def get_token_preview(self, obj):
        """Retourne un aperçu du token pour la sécurité"""
        if len(obj.token) > 20:
            return f"{obj.token[:10]}...{obj.token[-10:]}"
        return obj.token


class FCMTokenListSerializer(serializers.ModelSerializer):
    """Serializer simple pour la liste des tokens FCM"""
    token_preview = serializers.SerializerMethodField()

    class Meta:
        model = FCMToken
        fields = [
            'id', 'token_preview', 'platform', 'device_id',
            'is_active', 'last_used', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'last_used', 'token_preview']

    def get_token_preview(self, obj):
        if len(obj.token) > 20:
            return f"{obj.token[:10]}...{obj.token[-10:]}"
        return obj.token


class NotificationConfigSerializer(serializers.ModelSerializer):
    """Serializer pour la configuration des notifications"""

    class Meta:
        model = NotificationConfig
        fields = [
            'id', 'default_channel',
            'nexah_base_url', 'nexah_send_endpoint', 'nexah_credits_endpoint',
            'nexah_user', 'nexah_password', 'nexah_sender_id',
            'whatsapp_api_token', 'whatsapp_phone_number_id', 'whatsapp_business_id',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'nexah_password': {'write_only': True},
            'whatsapp_api_token': {'write_only': True}
        }