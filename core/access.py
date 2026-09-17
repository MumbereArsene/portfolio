from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import AccessLock


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR") or "0.0.0.0"


def lock_status(ip):
    lock = (
        AccessLock.objects.filter(ip_address=ip)
        .only("failures", "locked_until")
        .first()
    )
    limit = settings.ADMIN_LOGIN_ATTEMPTS
    if lock is None:
        return False, limit
    if lock.locked_until and lock.locked_until > timezone.now():
        return True, 0
    if lock.locked_until and lock.locked_until <= timezone.now():
        return False, limit
    return False, max(0, limit - lock.failures)


def is_locked(ip):
    locked, _remaining = lock_status(ip)
    return locked


def remaining_attempts(ip):
    _locked, remaining = lock_status(ip)
    return remaining


def register_failure(ip):
    lock, _ = AccessLock.objects.get_or_create(ip_address=ip)
    if lock.locked_until and lock.locked_until <= timezone.now():
        lock.failures = 0
        lock.locked_until = None
    lock.failures += 1
    remaining = max(0, settings.ADMIN_LOGIN_ATTEMPTS - lock.failures)
    if lock.failures >= settings.ADMIN_LOGIN_ATTEMPTS:
        lock.locked_until = timezone.now() + timedelta(minutes=settings.ADMIN_LOCK_MINUTES)
        remaining = 0
    lock.save(update_fields=["failures", "locked_until", "last_attempt"])
    return remaining


def register_success(ip):
    AccessLock.objects.filter(ip_address=ip).update(failures=0, locked_until=None)
