from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/cases/", include("apps.cases.urls")),
    path("api/action-plans/", include("apps.action_plans.urls")),
    path("api/reviews/", include("apps.reviews.urls")),
    path("api/translate/", include("apps.translation.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/dashboard/", include("apps.dashboard.urls")),
]

# Always serve media for the prototype, even when DEBUG is False
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
