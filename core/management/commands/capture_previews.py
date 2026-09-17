from django.core.management.base import BaseCommand

from core.models import Project
from core.previews import PreviewError, attach_homepage_preview


class Command(BaseCommand):
    help = "Capture l’accueil des projets qui ont un lien live."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true")

    def handle(self, *args, **options):
        projects = Project.objects.exclude(live_url="")
        if not options["force"]:
            projects = projects.filter(cover="")
        if not projects.exists():
            self.stdout.write("Aucun projet à capturer.")
            return
        for project in projects:
            try:
                attach_homepage_preview(project)
                self.stdout.write(self.style.SUCCESS(f"OK {project.title}"))
            except PreviewError as exc:
                self.stdout.write(self.style.WARNING(f"SKIP {project.title}: {exc}"))
