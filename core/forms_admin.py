from django.conf import settings
from django.contrib.admin.forms import AdminAuthenticationForm
from django.core.exceptions import ValidationError

from .access import is_locked, register_failure, register_success, client_ip


class LockedAdminAuthenticationForm(AdminAuthenticationForm):
    def clean(self):
        ip = client_ip(self.request)
        if is_locked(ip):
            raise ValidationError(
                f"Trop de tentatives. Accès bloqué {settings.ADMIN_LOCK_MINUTES} minutes.",
                code="locked",
            )
        try:
            cleaned = super().clean()
        except ValidationError as exc:
            remaining = register_failure(ip)
            if remaining <= 0:
                raise ValidationError(
                    f"3 tentatives échouées. Accès bloqué {settings.ADMIN_LOCK_MINUTES} minutes.",
                    code="locked",
                ) from exc
            raise ValidationError(
                f"Identifiants incorrects. {remaining} tentative(s) restante(s).",
                code="invalid_login",
            ) from exc
        register_success(ip)
        return cleaned
