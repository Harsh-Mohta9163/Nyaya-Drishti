from django.urls import path

from .views import (
    ActionPlanDetailView,
    ActionPlanListView,
    GenerateActionPlanView,
    GenerateRecommendationView,
    LCOExecutionDetailView,
    LCOExecutionListView,
)

urlpatterns = [
    path("", ActionPlanListView.as_view(), name="action-plan-list"),
    # Execution dashboard (LCO + dept-scoped users; central law sees all w/ ?department=)
    path("execution/", LCOExecutionListView.as_view(), name="execution-list"),
    path("execution/<uuid:pk>/", LCOExecutionDetailView.as_view(), name="execution-detail"),
    path("<uuid:pk>/", ActionPlanDetailView.as_view(), name="action-plan-detail"),
    path("<uuid:pk>/generate/", GenerateActionPlanView.as_view(), name="action-plan-generate"),
    path("<uuid:pk>/recommend/", GenerateRecommendationView.as_view(), name="action-plan-recommend-pk"),
    path("recommend/", GenerateRecommendationView.as_view(), name="action-plan-recommend"),
]
