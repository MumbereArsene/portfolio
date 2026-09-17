from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crée ou met à jour le compte atelier depuis ADMIN_USERNAME / ADMIN_PASSWORD."

    def handle(self, *args, **options):
        username = settings.ADMIN_USERNAME
        password = settings.ADMIN_PASSWORD
        email = settings.ADMIN_EMAIL or "arsene@example.com"
        if not username or not password:
            self.stdout.write(
                self.style.WARNING("ADMIN_USERNAME / ADMIN_PASSWORD absents — seeder ignoré.")
            )
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email},
        )
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()
        verb = "créé" if created else "mis à jour"
        self.stdout.write(self.style.SUCCESS(f"Compte atelier {verb} : {username}"))
