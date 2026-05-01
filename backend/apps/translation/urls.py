from django.urls import path

from .views import TranslateView

urlpatterns = [
    path("", TranslateView.as_view(), name="translate"),
]
