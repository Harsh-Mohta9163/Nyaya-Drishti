from django.urls import path

from .views import ExportTrainingDataView, PendingReviewsView, SubmitReviewView

urlpatterns = [
    path("pending/", PendingReviewsView.as_view(), name="pending-reviews"),
    path("<int:pk>/submit/", SubmitReviewView.as_view(), name="submit-review"),
    path("export-training/", ExportTrainingDataView.as_view(), name="export-training-data"),
]
