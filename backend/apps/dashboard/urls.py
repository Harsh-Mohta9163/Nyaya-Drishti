from django.urls import path

from .views import (
    DashboardByDepartmentView,
    DashboardDeadlinesView,
    DashboardHighRiskView,
    DashboardStatsView,
    NodalDeadlinesMonitorView,
)

urlpatterns = [
    path("stats/", DashboardStatsView.as_view(), name="dashboard-stats"),
    path("deadlines/", DashboardDeadlinesView.as_view(), name="dashboard-deadlines"),
    path("deadlines-monitor/", NodalDeadlinesMonitorView.as_view(), name="nodal-deadlines-monitor"),
    path("high-risk/", DashboardHighRiskView.as_view(), name="dashboard-high-risk"),
    path("by-department/", DashboardByDepartmentView.as_view(), name="dashboard-by-department"),
]
