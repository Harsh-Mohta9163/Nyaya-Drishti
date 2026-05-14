from django.urls import path

from .views import (
    CaseListCreateView,
    CaseDetailView,
    CaseDepartmentOverrideView,
    JudgmentUpdateView,
    CaseExtractView,
    CaseStatusView,
    ServePdfView,
    CaseActionPlanView,
    ActionPlanReviewView,
    AppealStrategyView,
    ReAnnotateSourceView,
)

urlpatterns = [
    path("", CaseListCreateView.as_view(), name="case-list-create"),
    path("<uuid:pk>/", CaseDetailView.as_view(), name="case-detail"),
    path("<uuid:pk>/department/", CaseDepartmentOverrideView.as_view(), name="case-department-override"),
    path("judgments/<uuid:pk>/", JudgmentUpdateView.as_view(), name="judgment-update"),
    path("<uuid:pk>/status/", CaseStatusView.as_view(), name="case-status"),
    path("extract/", CaseExtractView.as_view(), name="case-extract"),
    path("judgments/<uuid:pk>/pdf/", ServePdfView.as_view(), name="serve-pdf"),
    path("<uuid:pk>/action-plan/", CaseActionPlanView.as_view(), name="case-action-plan"),
    path("action-plans/<int:pk>/review/", ActionPlanReviewView.as_view(), name="action-plan-review"),
    path("<uuid:case_id>/judgments/<uuid:judgment_id>/appeal-strategy/", AppealStrategyView.as_view(), name="appeal-strategy"),
    path("<uuid:pk>/re-annotate/", ReAnnotateSourceView.as_view(), name="re-annotate-source"),
]
