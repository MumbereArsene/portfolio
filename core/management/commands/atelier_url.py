from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Affiche l’URL secrète de déverrouillage de l’atelier."

    def handle(self, *args, **options):
        path = f"/s/{settings.ADMIN_UNLOCK_TOKEN}/"
        self.stdout.write("Ouvre d’abord cette URL (jeton + session) :")
        self.stdout.write(self.style.WARNING(f"http://127.0.0.1:8000{path}"))
        self.stdout.write("Elle ouvre l’atelier (dashboard), pas l’admin Django.")
        self.stdout.write("/admin/ est volontairement introuvable.")
