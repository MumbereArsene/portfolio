from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("a-propos/", views.about, name="about"),
    path("competences/", views.skills, name="skills"),
    path("projets/", views.project_list, name="projects"),
    path("projets/<slug:slug>/", views.project_detail, name="project_detail"),
    path("certificats/", views.certificate_list, name="certificates"),
    path("certificats/<slug:slug>/", views.certificate_detail, name="certificate_detail"),
    path("certificats/<slug:slug>/consulter/", views.certificate_view, name="certificate_view"),
    path("certificats/<slug:slug>/telecharger/", views.certificate_download, name="certificate_download"),
    path("cv/", views.cv_list, name="cvs"),
    path("cv/<int:pk>/", views.cv_detail, name="cv_detail"),
    path("cv/<int:pk>/consulter/", views.cv_view, name="cv_view"),
    path("cv/<int:pk>/telecharger/", views.cv_download, name="cv_download"),
    path("contact/", views.contact, name="contact"),
    path("healthz", views.healthz, name="healthz"),
    path("manifest.webmanifest", views.web_manifest, name="manifest"),
    path("sw.js", views.service_worker, name="service_worker"),
    path("robots.txt", views.robots_txt, name="robots"),
    path("sitemap.xml", views.sitemap_xml, name="sitemap"),
]
