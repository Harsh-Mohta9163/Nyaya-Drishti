from django.urls import path

from .views import ActionPlanDetailView, ActionPlanListView, GenerateActionPlanView

urlpatterns = [
    path("", ActionPlanListView.as_view(), name="action-plan-list"),
    path("<int:pk>/", ActionPlanDetailView.as_view(), name="action-plan-detail"),
    path("<int:pk>/generate/", GenerateActionPlanView.as_view(), name="action-plan-generate"),
]
