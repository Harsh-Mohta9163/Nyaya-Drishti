from django.urls import path

from .views import (
    CaseActionPlanView,
    CaseDetailView,
    CaseExtractView,
    CaseListCreateView,
    CaseReviewHistoryView,
    CaseStatusUpdateView,
)

urlpatterns = [
    path("", CaseListCreateView.as_view(), name="case-list-create"),
    path("<int:pk>/", CaseDetailView.as_view(), name="case-detail"),
    path("<int:pk>/status/", CaseStatusUpdateView.as_view(), name="case-status"),
    path("<int:pk>/extract/", CaseExtractView.as_view(), name="case-extract"),
    path("<int:pk>/action-plan/", CaseActionPlanView.as_view(), name="case-action-plan"),
    path("<int:pk>/review-history/", CaseReviewHistoryView.as_view(), name="case-review-history"),
]
