from datetime import date

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import TestCase
from django.urls import reverse

from core.models import AccessLock, Certificate, ContactMessage, Curriculum, Profile, Project, Skill, SkillCategory, Tag
from core.previews import extract_og_image


class PortfolioTests(TestCase):
    def setUp(self):
        Profile.objects.create(
            display_name="Mumbere Siviwe",
            first_name="Siviwe",
            last_name="Mumbere",
            also_known_as="Arsène",
            headline="Test",
            bio="Bio",
            email="arsene@example.com",
        )
        Project.objects.create(
            title="Demo",
            slug="demo",
            excerpt="Extrait",
            description="Description",
            category=Project.Category.WEB,
            year=2026,
            published=True,
            featured=True,
        )
        category = SkillCategory.objects.create(name="Python")
        self.skill = Skill.objects.create(category=category, name="Django", level=70)
        pdf = ContentFile(b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n", name="doc.pdf")
        self.certificate = Certificate.objects.create(
            title="SQL",
            issuer="Cours",
            issued_on=date(2025, 5, 1),
            published=True,
            credential_url="https://example.com/cert/sql",
            course_url="https://example.com/cours/sql",
        )
        self.certificate.file.save("sql.pdf", pdf, save=True)
        self.cv = Curriculum.objects.create(
            title="CV Data",
            language="FR",
            published=True,
            is_primary=True,
        )
        self.cv.file.save("cv.pdf", ContentFile(b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n", name="cv.pdf"), save=True)

    def test_home_ok(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mumbere")
        self.assertContains(response, "Siviwe")
        self.assertContains(response, "Arsène")
        self.assertContains(response, 'name="robots"')
        self.assertContains(response, "application/ld+json")

    def test_healthz(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")

    def test_seo_files(self):
        robots = self.client.get(reverse("core:robots"))
        self.assertEqual(robots.status_code, 200)
        self.assertContains(robots, "Sitemap:")
        sitemap = self.client.get(reverse("core:sitemap"))
        self.assertEqual(sitemap.status_code, 200)
        self.assertContains(sitemap, "/projets/")

    def test_project_detail_ok(self):
        response = self.client.get(reverse("core:project_detail", args=["demo"]))
        self.assertEqual(response.status_code, 200)

    def test_contact_saves_message(self):
        response = self.client.post(
            reverse("core:contact"),
            {
                "name": "Léa",
                "email": "lea@example.com",
                "phone": "243812345678",
                "subject": "Collaboration",
                "message": "On peut en parler ?",
            },
        )
        self.assertEqual(response.status_code, 302)
        saved = ContactMessage.objects.get(email="lea@example.com")
        self.assertEqual(saved.phone, "243812345678")
        self.assertIn("wa.me/243812345678", saved.whatsapp_url)

    def test_public_menu_drawer_markup(self):
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "data-nav")
        self.assertContains(response, "site-scrim")
        self.assertContains(response, "site-menu")

    def test_skill_level_change_is_logged(self):
        self.skill.level = 78
        self.skill.save()
        self.assertGreaterEqual(self.skill.history.count(), 2)
        self.assertEqual(self.skill.latest_delta, 8)

    def test_certificates_and_cv_pages(self):
        self.assertEqual(self.client.get(reverse("core:certificates")).status_code, 200)
        self.assertEqual(self.client.get(self.certificate.get_absolute_url()).status_code, 200)
        detail = self.client.get(self.certificate.get_absolute_url())
        self.assertContains(detail, "Lien du certificat")
        self.assertContains(detail, "Formation en ligne")
        self.assertEqual(self.client.get(reverse("core:cvs")).status_code, 200)
        self.assertEqual(self.client.get(self.cv.get_absolute_url()).status_code, 200)
        download = self.client.get(reverse("core:cv_download", args=[self.cv.pk]))
        self.assertEqual(download.status_code, 200)
        self.assertIn("attachment", download.get("Content-Disposition", ""))
        view = self.client.get(reverse("core:cv_view", args=[self.cv.pk]))
        self.assertEqual(view.status_code, 200)
        self.assertIn("inline", view.get("Content-Disposition", ""))


class AtelierSecurityTests(TestCase):
    def test_public_admin_path_is_hidden(self):
        self.assertEqual(self.client.get("/admin/").status_code, 404)
        self.assertEqual(self.client.get("/admin/login/").status_code, 404)
        self.assertEqual(self.client.get("/" + settings.ADMIN_URL_PATH).status_code, 404)

    def test_login_page_is_reachable(self):
        login_page = self.client.get(reverse("studio:login"))
        self.assertEqual(login_page.status_code, 200)
        self.assertContains(login_page, "Atelier")

    def test_wrong_token_is_hidden(self):
        self.assertEqual(self.client.get("/s/wrong-token/").status_code, 404)

    def test_valid_token_opens_login_not_django_admin(self):
        response = self.client.get(reverse("atelier_unlock", args=[settings.ADMIN_UNLOCK_TOKEN]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("studio:login"))
        login_page = self.client.get(reverse("studio:login"))
        self.assertEqual(login_page.status_code, 200)
        self.assertContains(login_page, "Atelier")
        self.assertNotContains(login_page, "Django administration")
        self.assertNotContains(login_page, "fonts.googleapis.com")
        self.assertContains(login_page, "data-pwa-install")
        self.assertContains(login_page, "Installer l’app")
        self.assertEqual(AccessLock.objects.count(), 0)
        manifest = self.client.get(reverse("core:manifest"))
        self.assertEqual(manifest.status_code, 200)
        self.assertEqual(manifest.json()["short_name"], "Atelier")

    def test_three_failed_logins_then_lock(self):
        User.objects.create_superuser("arsene", "arsene@example.com", "correct-pass")
        self.client.get(reverse("atelier_unlock", args=[settings.ADMIN_UNLOCK_TOKEN]))
        login_url = reverse("studio:login")
        for _ in range(settings.ADMIN_LOGIN_ATTEMPTS):
            response = self.client.post(login_url, {"username": "arsene", "password": "bad"})
            self.assertEqual(response.status_code, 200)
        locked = self.client.post(login_url, {"username": "arsene", "password": "correct-pass"})
        self.assertEqual(locked.status_code, 200)
        self.assertContains(locked, "bloqué")


class StudioCrudTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("arsene", "arsene@example.com", "correct-pass")
        self.client.get(reverse("atelier_unlock", args=[settings.ADMIN_UNLOCK_TOKEN]))
        self.client.post(reverse("studio:login"), {"username": "arsene", "password": "correct-pass"})

    def test_dashboard(self):
        response = self.client.get(reverse("studio:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Vue d’ensemble")
        self.assertContains(response, "data-menu")
        self.assertContains(response, "studio-scrim")
        self.assertNotContains(response, "studio-sidebar")

    def test_message_shows_email_and_whatsapp(self):
        message = ContactMessage.objects.create(
            name="Léa",
            email="lea@example.com",
            phone="243812345678",
            subject="Collab",
            message="Salut",
        )
        listing = self.client.get(reverse("studio:messages"))
        self.assertContains(listing, "lea@example.com")
        self.assertContains(listing, "wa.me/243812345678")
        detail = self.client.get(reverse("studio:message_detail", args=[message.pk]))
        self.assertContains(detail, "Répondre par email")
        self.assertContains(detail, "Répondre sur WhatsApp")

    def test_logout_returns_to_login_and_drops_auth(self):
        response = self.client.post(reverse("studio:logout"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("studio:login"))
        login_page = self.client.get(reverse("studio:login"))
        self.assertEqual(login_page.status_code, 200)
        dashboard = self.client.get(reverse("studio:home"))
        self.assertEqual(dashboard.status_code, 302)
        self.assertEqual(dashboard.url, reverse("studio:login"))

    def test_project_tags_filtered_by_category(self):
        django_tag = Tag.objects.create(name="Django", categories=["web", "vibe"])
        torch_tag = Tag.objects.create(name="PyTorch", categories=["deep"])
        form_page = self.client.get(reverse("studio:create", args=["projets"]))
        self.assertContains(form_page, 'data-categories="web vibe"')
        self.assertContains(form_page, 'data-categories="deep"')
        self.assertContains(form_page, django_tag.name)
        self.assertContains(form_page, torch_tag.name)

    def test_project_crud(self):
        create = self.client.post(
            reverse("studio:create", args=["projets"]),
            {
                "title": "Plateforme X",
                "excerpt": "Une plateforme",
                "description": "Détail du projet",
                "category": Project.Category.WEB,
                "year": 2026,
                "accent": "#d4ff4a",
                "order": 0,
            },
        )
        self.assertEqual(create.status_code, 302)
        project = Project.objects.get(title="Plateforme X")
        listing = self.client.get(reverse("studio:list", args=["projets"]))
        self.assertContains(listing, "Plateforme X")
        update = self.client.post(
            reverse("studio:update", args=["projets", project.pk]),
            {
                "title": "Plateforme X2",
                "excerpt": "Une plateforme",
                "description": "Détail du projet",
                "category": Project.Category.WEB,
                "year": 2026,
                "accent": "#d4ff4a",
                "order": 0,
                "published": "on",
            },
        )
        self.assertEqual(update.status_code, 302)
        project.refresh_from_db()
        self.assertEqual(project.title, "Plateforme X2")
        delete = self.client.post(reverse("studio:delete", args=["projets", project.pk]))
        self.assertEqual(delete.status_code, 302)
        self.assertFalse(Project.objects.filter(pk=project.pk).exists())


class PreviewHelperTests(TestCase):
    def test_og_image_is_extracted(self):
        html = '<html><meta property="og:image" content="/img/home.png"></html>'
        self.assertEqual(extract_og_image(html, "https://itipbumbu.com/"), "https://itipbumbu.com/img/home.png")
