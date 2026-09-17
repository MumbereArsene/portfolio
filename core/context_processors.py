import json

from django.conf import settings

from .models import Certificate, Curriculum, Profile


def site_profile(request):
    path = request.path
    if (
        path.startswith(f"/{settings.ADMIN_URL_PATH}")
        or path.startswith("/s/")
        or path in {"/manifest.webmanifest", "/sw.js", "/healthz"}
    ):
        return {}

    profile = Profile.objects.only(
        "display_name",
        "also_known_as",
        "headline",
        "tagline",
        "email",
        "github",
        "linkedin",
        "photo",
        "last_name",
        "availability",
    ).first()
    host = f"{request.scheme}://{request.get_host()}"
    person = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": getattr(profile, "display_name", None) or "Mumbere Siviwe",
        "alternateName": [
            getattr(profile, "also_known_as", None) or "Arsène",
            "Arsene",
            "Arsène Mumbere",
            "Mumbere Arsène",
            "Siviwe Mumbere",
        ],
        "jobTitle": getattr(profile, "headline", None) or "Étudiant math-info",
        "description": getattr(profile, "tagline", None) or "Portfolio math-info, data et Django.",
        "url": f"{host}/",
    }
    if profile and profile.photo:
        person["image"] = f"{host}{profile.photo.url}"
    if profile and profile.email:
        person["email"] = profile.email
    same_as = []
    if profile and profile.github:
        same_as.append(profile.github)
    if profile and profile.linkedin:
        same_as.append(profile.linkedin)
    if same_as:
        person["sameAs"] = same_as
    return {
        "profile": profile,
        "primary_cv": Curriculum.objects.filter(published=True, is_primary=True).only("id", "file").first(),
        "cv_count": Curriculum.objects.filter(published=True).count(),
        "certificate_count": Certificate.objects.filter(published=True).count(),
        "person_jsonld": json.dumps(person, ensure_ascii=False),
        "site_url": getattr(settings, "SITE_URL", host),
    }
