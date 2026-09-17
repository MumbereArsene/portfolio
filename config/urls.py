from django.conf import settings
from django.http import Http404
from django.urls import include, path, re_path
from django.views.static import serve

from core.views import unlock_atelier


def decoy_admin(_request):
    raise Http404()


urlpatterns = [
    path("admin/", decoy_admin),
    path("s/<str:token>/", unlock_atelier, name="atelier_unlock"),
    path(settings.ADMIN_URL_PATH, include("core.studio_urls")),
    path("", include("core.urls")),
]

if settings.DEBUG or settings.SERVE_MEDIA:
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    ]
