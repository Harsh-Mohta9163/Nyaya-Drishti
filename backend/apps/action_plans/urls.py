from django.urls import path

from .views import ActionPlanDetailView, ActionPlanListView, GenerateActionPlanView, GenerateRecommendationView

urlpatterns = [
    path("", ActionPlanListView.as_view(), name="action-plan-list"),
    path("<int:pk>/", ActionPlanDetailView.as_view(), name="action-plan-detail"),
    path("<int:pk>/generate/", GenerateActionPlanView.as_view(), name="action-plan-generate"),
    path("<int:pk>/recommend/", GenerateRecommendationView.as_view(), name="action-plan-recommend-pk"),
    path("recommend/", GenerateRecommendationView.as_view(), name="action-plan-recommend"),
]
