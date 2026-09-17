import hmac

from django.conf import settings
from django.contrib import messages
from django.db.models import Count, Prefetch
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET

from .files import serve_pdf
from .forms import ContactForm
from .models import (
    Certificate,
    Curriculum,
    Focus,
    Milestone,
    Project,
    SiteStat,
    Skill,
    SkillCategory,
)


def _skill_categories():
    return SkillCategory.objects.prefetch_related(
        Prefetch("skills", queryset=Skill.objects.prefetch_related("history"))
    )


def home(request):
    projects = Project.objects.filter(published=True, featured=True)[:4]
    focuses = Focus.objects.all()
    stats = SiteStat.objects.all()
    categories = _skill_categories()
    milestones = Milestone.objects.all()[:4]
    certificates = Certificate.objects.filter(published=True, featured=True)[:3]
    cvs = Curriculum.objects.filter(published=True)[:3]
    return render(
        request,
        "core/home.html",
        {
            "projects": projects,
            "focuses": focuses,
            "stats": stats,
            "categories": categories,
            "milestones": milestones,
            "certificates": certificates,
            "cvs": cvs,
        },
    )


def about(request):
    focuses = Focus.objects.all()
    categories = _skill_categories()
    milestones = Milestone.objects.all()
    stats = SiteStat.objects.all()
    return render(
        request,
        "core/about.html",
        {
            "focuses": focuses,
            "categories": categories,
            "milestones": milestones,
            "stats": stats,
        },
    )


def skills(request):
    categories = _skill_categories()
    recent = (
        Skill.objects.select_related("category")
        .prefetch_related("history")
        .order_by("-updated_at")[:8]
    )
    return render(
        request,
        "core/skills.html",
        {"categories": categories, "recent": recent},
    )


def project_list(request):
    category = request.GET.get("cat", "")
    projects = Project.objects.filter(published=True)
    if category in Project.Category.values:
        projects = projects.filter(category=category)
    counts = {
        row["category"]: row["total"]
        for row in Project.objects.filter(published=True)
        .values("category")
        .annotate(total=Count("id"))
    }
    category_filters = [
        {"value": value, "label": label, "count": counts.get(value, 0)}
        for value, label in Project.Category.choices
    ]
    return render(
        request,
        "core/projects.html",
        {
            "projects": projects,
            "active_category": category,
            "category_filters": category_filters,
            "total": Project.objects.filter(published=True).count(),
        },
    )


def project_detail(request, slug):
    project = get_object_or_404(Project, slug=slug, published=True)
    related = (
        Project.objects.filter(published=True, category=project.category)
        .exclude(pk=project.pk)[:3]
    )
    return render(
        request,
        "core/project_detail.html",
        {"project": project, "related": related},
    )


def certificate_list(request):
    certificates = Certificate.objects.filter(published=True)
    return render(request, "core/certificates.html", {"certificates": certificates})


def certificate_detail(request, slug):
    certificate = get_object_or_404(Certificate, slug=slug, published=True)
    related = (
        Certificate.objects.filter(published=True, kind=certificate.kind)
        .exclude(pk=certificate.pk)[:3]
    )
    return render(
        request,
        "core/certificate_detail.html",
        {"certificate": certificate, "related": related},
    )


def certificate_download(request, slug):
    certificate = get_object_or_404(Certificate, slug=slug, published=True)
    return serve_pdf(certificate.file, download=True, fallback_name=certificate.title)


def certificate_view(request, slug):
    certificate = get_object_or_404(Certificate, slug=slug, published=True)
    return serve_pdf(certificate.file, download=False, fallback_name=certificate.title)


def cv_list(request):
    cvs = Curriculum.objects.filter(published=True)
    return render(request, "core/cvs.html", {"cvs": cvs})


def cv_detail(request, pk):
    cv = get_object_or_404(Curriculum, pk=pk, published=True)
    others = Curriculum.objects.filter(published=True).exclude(pk=cv.pk)
    return render(request, "core/cv_detail.html", {"cv": cv, "others": others})


def cv_download(request, pk):
    cv = get_object_or_404(Curriculum, pk=pk, published=True)
    return serve_pdf(cv.file, download=True, fallback_name=cv.title)


def cv_view(request, pk):
    cv = get_object_or_404(Curriculum, pk=pk, published=True)
    return serve_pdf(cv.file, download=False, fallback_name=cv.title)


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Message reçu. Je te réponds dès que je sors du terminal.",
            )
            return redirect("core:contact")
    else:
        form = ContactForm()
    return render(request, "core/contact.html", {"form": form})


@require_GET
def unlock_atelier(request, token):
    expected = settings.ADMIN_UNLOCK_TOKEN.encode()
    given = token.encode()
    if not hmac.compare_digest(given, expected):
        raise Http404()
    request.session.cycle_key()
    request.session[settings.ADMIN_SESSION_KEY] = True
    request.session.set_expiry(60 * 60 * 8)
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("studio:home")
    return redirect("studio:login")


@require_GET
def robots_txt(request):
    host = f"{request.scheme}://{request.get_host()}"
    body = "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "Disallow: /admin/",
            "Disallow: /s/",
            f"Sitemap: {host}/sitemap.xml",
            "",
        ]
    )
    return HttpResponse(body, content_type="text/plain")


@require_GET
def sitemap_xml(request):
    host = f"{request.scheme}://{request.get_host()}"
    paths = ["/", "/a-propos/", "/competences/", "/projets/", "/certificats/", "/cv/", "/contact/"]
    paths += [project.get_absolute_url() for project in Project.objects.filter(published=True)]
    paths += [cert.get_absolute_url() for cert in Certificate.objects.filter(published=True)]
    urls = "".join(
        f"<url><loc>{host}{path}</loc><changefreq>weekly</changefreq></url>" for path in paths
    )
    xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>'
    return HttpResponse(xml, content_type="application/xml")


@require_GET
def healthz(_request):
    return HttpResponse("ok", content_type="text/plain")


@require_GET
def web_manifest(request):
    icon_192 = request.build_absolute_uri("/static/icons/atelier-192.png")
    icon_512 = request.build_absolute_uri("/static/icons/atelier-512.png")
    payload = {
        "name": "Atelier",
        "short_name": "Atelier",
        "description": "Espace d’administration du portfolio.",
        "start_url": f"/{settings.ADMIN_URL_PATH}connexion/",
        "scope": "/",
        "display": "standalone",
        "background_color": "#07080b",
        "theme_color": "#07080b",
        "icons": [
            {"src": icon_192, "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": icon_512, "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
    }
    return JsonResponse(payload, content_type="application/manifest+json")


@require_GET
def service_worker(request):
    path = settings.BASE_DIR / "static" / "js" / "sw.js"
    response = HttpResponse(path.read_text(encoding="utf-8"), content_type="text/javascript")
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"
    return response
