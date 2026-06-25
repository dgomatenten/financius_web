from django.urls import path

from .views import (
    AmortizationDetailView,
    AmortizationListView,
    AnalyticsBLSView,
    AnalyticsCalendarView,
    AnalyticsCategoryBreakdownView,
    AnalyticsInsightsView,
    AnalyticsSummaryView,
    AnalyticsYoYView,
    BudgetListView,
    BudgetProgressView,
    CardDetailView,
    CardListView,
    CategoryDetailView,
    CategoryListView,
    CategoryMappingDetailView,
    CategoryMappingListView,
    ExportView,
    PairingQRView,
    PairingValidateView,
    ReceiptAmazonImportView,
    ReceiptBulkView,
    ReceiptDetailView,
    ReceiptListView,
    RecurringListView,
    ShopListView,
    ShopMergeView,
    SyncStatusView,
    SyncView,
)

urlpatterns = [
    # Receipts
    path("receipts/", ReceiptListView.as_view()),
    path("receipts/bulk/", ReceiptBulkView.as_view()),
    path("receipts/import/amazon/", ReceiptAmazonImportView.as_view()),
    path("receipts/<str:receipt_id>/", ReceiptDetailView.as_view()),

    # Sync
    path("sync/", SyncView.as_view()),
    path("sync/status/", SyncStatusView.as_view()),

    # Master data — categories
    path("master-data/categories/", CategoryListView.as_view()),
    path("master-data/categories/<str:category_id>/", CategoryDetailView.as_view()),

    # Master data — shops
    path("master-data/shops/", ShopListView.as_view()),
    path("master-data/shops/<str:shop_id>/merge/", ShopMergeView.as_view()),

    # Master data — cards
    path("master-data/cards/", CardListView.as_view()),
    path("master-data/cards/<str:card_id>/", CardDetailView.as_view()),

    # Master data — category mappings
    path("master-data/category-mappings/", CategoryMappingListView.as_view()),
    path("master-data/category-mappings/<str:mapping_id>/", CategoryMappingDetailView.as_view()),

    # Budgets
    path("budgets/", BudgetListView.as_view()),
    path("budgets/progress/", BudgetProgressView.as_view()),

    # Pairing
    path("pairing/qr/", PairingQRView.as_view()),
    path("pairing/validate/", PairingValidateView.as_view()),

    # Analytics
    path("analytics/summary/", AnalyticsSummaryView.as_view()),
    path("analytics/category-breakdown/", AnalyticsCategoryBreakdownView.as_view()),
    path("analytics/calendar/", AnalyticsCalendarView.as_view()),
    path("analytics/yoy/", AnalyticsYoYView.as_view()),
    path("analytics/benchmarks/bls/", AnalyticsBLSView.as_view()),
    path("analytics/insights/", AnalyticsInsightsView.as_view()),

    # Recurring
    path("recurring/", RecurringListView.as_view()),

    # Export
    path("export/", ExportView.as_view()),

    # Amortization
    path("amortization/", AmortizationListView.as_view()),
    path("amortization/<str:rule_id>/", AmortizationDetailView.as_view()),
]
