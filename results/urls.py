from django.urls import path
from .views import (
    ElectionResultsView,
    PositionResultsView,
    LiveResultsView,
    ExportResultsCSVView,
    ExportResultsPDFView,
    DashboardView
)

urlpatterns = [
    path('', ElectionResultsView.as_view(), name='election_results'),
    path('dashboard/', DashboardView.as_view(), name='results_dashboard'),
    path('election/<int:election_id>/', PositionResultsView.as_view(), name='position_results'),
    path('election/<int:election_id>/live/', LiveResultsView.as_view(), name='live_results'),
    path('election/<int:election_id>/export/csv/', ExportResultsCSVView.as_view(), name='export_csv'),
    path('election/<int:election_id>/export/pdf/', ExportResultsPDFView.as_view(), name='export_pdf'),
]
