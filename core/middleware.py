from django.conf import settings
from django.http import Http404


def _studio_open_paths():
    prefix = f"/{settings.ADMIN_URL_PATH}"
    return {f"{prefix}connexion/", f"{prefix}deconnexion/"}


class AdminGateMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        admin_prefix = f"/{settings.ADMIN_URL_PATH}"
        if request.path.startswith(admin_prefix) and request.path not in _studio_open_paths():
            if not request.session.get(settings.ADMIN_SESSION_KEY):
                raise Http404()
        return self.get_response(request)
