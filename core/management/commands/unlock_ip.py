from django.core.management.base import BaseCommand

from core.models import AccessLock


class Command(BaseCommand):
    help = "Débloque une adresse IP verrouillée."

    def add_arguments(self, parser):
        parser.add_argument("ip")

    def handle(self, *args, **options):
        updated = AccessLock.objects.filter(ip_address=options["ip"]).update(
            failures=0, locked_until=None
        )
        if updated:
            self.stdout.write(self.style.SUCCESS(f"IP {options['ip']} débloquée."))
        else:
            self.stdout.write("Aucune entrée pour cette IP.")
