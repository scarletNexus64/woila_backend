from rest_framework import serializers
from .models import Wallet, WalletTransaction


class WalletSerializer(serializers.ModelSerializer):
    """Serializer pour le portefeuille"""
    user_info = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = [
            'id', 'user_type', 'user_id', 'user_info',
            'balance', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user_info']

    def get_user_info(self, obj):
        return f"{obj.user_type.model} {obj.user_id}"


class WalletTransactionSerializer(serializers.ModelSerializer):
    """Serializer pour les transactions du portefeuille"""
    user_info = serializers.SerializerMethodField()
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = WalletTransaction
        fields = [
            'id', 'reference', 'user_type', 'user_id', 'user_info',
            'transaction_type', 'transaction_type_display',
            'amount', 'status', 'status_display',
            'payment_method', 'phone_number',
            'freemopay_reference', 'freemopay_external_id',
            'balance_before', 'balance_after',
            'description', 'metadata',
            'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'reference', 'created_at', 'updated_at',
            'completed_at', 'user_info', 'transaction_type_display',
            'status_display', 'balance_before', 'balance_after'
        ]

    def get_user_info(self, obj):
        return f"{obj.user_type.model} {obj.user_id}"


class WalletDepositSerializer(serializers.Serializer):
    """Serializer pour les dépôts"""
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=100.00
    )
    phone_number = serializers.CharField(max_length=15)
    description = serializers.CharField(max_length=255, required=False)


class WalletWithdrawalSerializer(serializers.Serializer):
    """Serializer pour les retraits"""
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=100.00
    )
    phone_number = serializers.CharField(max_length=15)
    description = serializers.CharField(max_length=255, required=False)


class WalletTransactionListSerializer(serializers.ModelSerializer):
    """Serializer simple pour la liste des transactions"""
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = WalletTransaction
        fields = [
            'id', 'reference', 'transaction_type', 'transaction_type_display',
            'amount', 'status', 'status_display',
            'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'transaction_type_display', 'status_display']