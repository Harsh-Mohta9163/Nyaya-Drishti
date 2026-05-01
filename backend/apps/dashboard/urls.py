from django.urls import path

from .views import DashboardDeadlinesView, DashboardHighRiskView, DashboardStatsView

urlpatterns = [
    path("stats/", DashboardStatsView.as_view(), name="dashboard-stats"),
    path("deadlines/", DashboardDeadlinesView.as_view(), name="dashboard-deadlines"),
    path("high-risk/", DashboardHighRiskView.as_view(), name="dashboard-high-risk"),
]