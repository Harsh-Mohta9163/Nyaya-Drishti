from django.urls import path

from .views import (
    CaseActionPlanView,
    CaseDetailView,
    CaseExtractionView,
    CaseExtractView,
    CaseListCreateView,
    CasePDFView,
    CaseReviewHistoryView,
    CaseReviewSubmitView,
    CaseStatusUpdateView,
)

urlpatterns = [
    path("", CaseListCreateView.as_view(), name="case-list-create"),
    path("<int:pk>/", CaseDetailView.as_view(), name="case-detail"),
    path("<int:pk>/status/", CaseStatusUpdateView.as_view(), name="case-status"),
    path("<int:pk>/extract/", CaseExtractView.as_view(), name="case-extract"),
    path("<int:pk>/extraction/", CaseExtractionView.as_view(), name="case-extraction"),
    path("<int:pk>/action-plan/", CaseActionPlanView.as_view(), name="case-action-plan"),
    path("<int:pk>/action-plan/generate/", CaseActionPlanView.as_view(), name="case-action-plan-generate"),
    path("<int:pk>/pdf/", CasePDFView.as_view(), name="case-pdf"),
    path("<int:pk>/review/", CaseReviewSubmitView.as_view(), name="case-review-submit"),
    path("<int:pk>/review-history/", CaseReviewHistoryView.as_view(), name="case-review-history"),
]
