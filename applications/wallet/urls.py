# EXISTING ENDPOINTS - DO NOT MODIFY URLs - Already integrated in production
# Wallet management URLs for the Woila VTC platform

from django.urls import path
from . import views

app_name = 'wallet'

urlpatterns = [
    # EXISTING ENDPOINT: GET /api/wallet/balance/ - DO NOT MODIFY
    path('balance/', views.WalletBalanceView.as_view(), name='wallet-balance'),
    
    # EXISTING ENDPOINT: POST /api/wallet/deposit/ - DO NOT MODIFY
    path('deposit/', views.WalletDepositView.as_view(), name='wallet-deposit'),
    
    # EXISTING ENDPOINT: POST /api/wallet/withdrawal/ - DO NOT MODIFY
    path('withdrawal/', views.WalletWithdrawalView.as_view(), name='wallet-withdrawal'),
    
    # EXISTING ENDPOINT: GET /api/wallet/transactions/ - DO NOT MODIFY
    path('transactions/', views.WalletTransactionHistoryView.as_view(), name='wallet-transactions'),
    
    # EXISTING ENDPOINT: GET /api/wallet/transactions/{reference}/ - DO NOT MODIFY
    path('transactions/<str:reference>/', views.WalletTransactionDetailView.as_view(), name='wallet-transaction-detail'),
    
    # EXISTING ENDPOINT: GET /api/wallet/transactions/{reference}/check-status/ - DO NOT MODIFY
    path('transactions/<str:reference>/check-status/', views.WalletTransactionStatusView.as_view(), name='wallet-transaction-status'),
]