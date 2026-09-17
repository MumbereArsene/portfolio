from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.html import format_html
from django.views.decorators.http import require_POST

from .access import client_ip, lock_status, register_failure, register_success
from .models import AccessLock, Certificate, ContactMessage, Curriculum, Profile, Project, Skill
from .previews import PreviewError, attach_homepage_preview
from .studio_catalog import CATALOG, get_resource
from .studio_forms import ProfileForm, StudioLoginForm


NAV = (
    ("studio:home", "Vue d’ensemble", None),
    ("studio:list", "Projets", "projets"),
    ("studio:list", "Certificats", "certificats"),
    ("studio:list", "CV", "cv"),
    ("studio:list", "Compétences", "competences"),
    ("studio:list", "Catégories", "categories"),
    ("studio:list", "Parcours", "parcours"),
    ("studio:list", "Axes", "axes"),
    ("studio:list", "Stats", "stats"),
    ("studio:list", "Tags", "tags"),
    ("studio:messages", "Messages", None),
    ("studio:profile", "Profil", None),
    ("studio:locks", "Sécurité", None),
)


def _open_studio_session(request):
    request.session[settings.ADMIN_SESSION_KEY] = True
    request.session.set_expiry(60 * 60 * 8)


def studio_gate(*, allow_anonymous=False):
    def decorator(view):
        def wrapped(request, *args, **kwargs):
            if not allow_anonymous and not request.session.get(settings.ADMIN_SESSION_KEY):
                raise Http404()
            if not allow_anonymous and (not request.user.is_authenticated or not request.user.is_staff):
                return redirect("studio:login")
            return view(request, *args, **kwargs)

        return wrapped

    return decorator


_NAV_CACHE = None


def _nav_spec():
    global _NAV_CACHE
    if _NAV_CACHE is None:
        _NAV_CACHE = [
            (name, label, resource, reverse(name, args=[resource] if resource else []))
            for name, label, resource in NAV
        ]
    return _NAV_CACHE


def _nav(request, unread=0):
    items = []
    for name, label, resource, url in _nav_spec():
        active = request.path == url or (resource and request.path.startswith(url))
        items.append(
            {
                "label": label,
                "url": url,
                "resource": resource,
                "active": active,
                "unread": unread if name == "studio:messages" else 0,
            }
        )
    return items


def _ctx(request, **extra):
    unread = extra.pop("unread", None)
    if unread is None:
        unread = ContactMessage.objects.filter(is_read=False).count()
    payload = {"nav_items": _nav(request, unread), "atelier_user": request.user, "unread": unread}
    payload.update(extra)
    return payload


def _cell(obj, attr, kind):
    value = getattr(obj, attr, "")
    if kind == "image":
        url = getattr(value, "url", "") if value else ""
        if url:
            return format_html('<img class="thumb" src="{}" alt="">', url)
        return "—"
    if kind == "bool":
        return format_html('<span class="pill {}">{}</span>', "on" if value else "off", "oui" if value else "non")
    if kind == "percent":
        return f"{value}%"
    if kind == "date":
        return value.strftime("%d/%m/%Y") if value else "—"
    if kind == "choice":
        display = getattr(obj, f"get_{attr}_display", None)
        return display() if display else value
    return value or "—"


@studio_gate(allow_anonymous=True)
def login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("studio:home")
    ip = client_ip(request)
    locked, remaining = lock_status(ip)
    form = StudioLoginForm(request, data=request.POST or None)
    error = ""
    if request.method == "POST":
        if locked:
            error = f"Trop de tentatives. Accès bloqué {settings.ADMIN_LOCK_MINUTES} minutes."
        elif form.is_valid():
            user = form.get_user()
            if not user.is_staff:
                remaining = register_failure(ip)
                error = "Ce compte n’a pas accès à l’atelier."
                locked = remaining <= 0
            else:
                login(request, user)
                _open_studio_session(request)
                register_success(ip)
                return redirect("studio:home")
        elif request.POST.get("username") and request.POST.get("password"):
            remaining = register_failure(ip)
            locked = remaining <= 0
            if remaining <= 0:
                error = f"3 tentatives échouées. Accès bloqué {settings.ADMIN_LOCK_MINUTES} minutes."
            else:
                error = f"Identifiants incorrects. {remaining} tentative(s) restante(s)."
        else:
            error = "Identifiant et mot de passe requis."
    return render(
        request,
        "studio/login.html",
        {
            "form": form,
            "error": error,
            "locked": locked,
            "remaining": remaining,
        },
    )


@require_POST
@studio_gate(allow_anonymous=True)
def logout_view(request):
    logout(request)
    _open_studio_session(request)
    return redirect("studio:login")


@studio_gate()
def dashboard(request):
    unread = ContactMessage.objects.filter(is_read=False).count()
    published = Project.objects.aggregate(total=Count("id"), live=Count("id", filter=Q(published=True)))
    return render(
        request,
        "studio/dashboard.html",
        _ctx(
            request,
            unread=unread,
            title="Vue d’ensemble",
            counts={
                "projets": published["total"],
                "publies": published["live"],
                "certificats": Certificate.objects.count(),
                "cv": Curriculum.objects.count(),
                "competences": Skill.objects.count(),
                "messages": unread,
            },
            recent_projects=Project.objects.only("id", "title", "year", "published")[:5],
            recent_messages=ContactMessage.objects.only("id", "name", "subject", "created_at", "is_read")[:5],
        ),
    )


@studio_gate()
def profile_view(request):
    profile = Profile.objects.first()
    if profile is None:
        profile = Profile.objects.create(
            display_name="Mumbere Siviwe",
            first_name="Siviwe",
            last_name="Mumbere",
            also_known_as="Arsène",
            headline="Portfolio",
            bio="",
            email="arsene@example.com",
        )
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour.")
            return redirect("studio:profile")
    else:
        form = ProfileForm(instance=profile)
    return render(request, "studio/form.html", _ctx(request, title="Profil public", form=form, resource=None, object=profile, mode="edit"))


@studio_gate()
def resource_list(request, resource):
    spec = get_resource(resource)
    if spec is None:
        raise Http404()
    queryset = spec.model.objects.all()
    if spec.key == "competences":
        queryset = queryset.select_related("category")
    elif spec.key == "projets":
        queryset = queryset.defer("description", "excerpt")
    query = request.GET.get("q", "").strip()
    if query and spec.search_fields:
        lookup = Q()
        for field_name in spec.search_fields:
            lookup |= Q(**{f"{field_name}__icontains": query})
        queryset = queryset.filter(lookup)
    if request.method == "POST":
        action = request.POST.get("action")
        ids = request.POST.getlist("ids")
        selected = spec.model.objects.filter(pk__in=ids)
        if action == "delete" and spec.can_delete:
            count = selected.count()
            selected.delete()
            messages.success(request, f"{count} élément(s) supprimé(s).")
        elif action == "publish" and hasattr(spec.model, "published"):
            selected.update(published=True)
            messages.success(request, "Publication mise à jour.")
        elif action == "unpublish" and hasattr(spec.model, "published"):
            selected.update(published=False)
            messages.success(request, "Éléments dépubliés.")
        return redirect("studio:list", resource=resource)
    paginator = Paginator(queryset, 12)
    page = paginator.get_page(request.GET.get("page"))
    rows = []
    for obj in page:
        rows.append(
            {
                "object": obj,
                "pk": obj.pk,
                "cells": [(_cell(obj, attr, kind), kind) for attr, _label, kind in spec.columns],
            }
        )
    return render(
        request,
        "studio/list.html",
        _ctx(
            request,
            title=spec.title,
            spec=spec,
            page=page,
            rows=rows,
            query=query,
            has_published=hasattr(spec.model, "published"),
        ),
    )


@studio_gate()
def resource_form(request, resource, pk=None):
    spec = get_resource(resource)
    if spec is None:
        raise Http404()
    instance = get_object_or_404(spec.model, pk=pk) if pk else None
    if instance is None and not spec.can_create:
        raise Http404()
    if request.method == "POST":
        form = spec.form_class(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            obj = form.save()
            if spec.key == "projets":
                if form.cleaned_data.get("refresh_preview") and obj.live_url:
                    try:
                        attach_homepage_preview(obj)
                        messages.success(request, "Projet enregistré et aperçu d’accueil capturé.")
                    except PreviewError as exc:
                        messages.warning(request, f"Projet enregistré, aperçu non capturé : {exc}")
                else:
                    messages.success(request, "Projet enregistré.")
            else:
                messages.success(request, f"{spec.singular.capitalize()} enregistré.")
            return redirect("studio:list", resource=resource)
    else:
        form = spec.form_class(instance=instance)
    history = []
    if spec.key == "competences" and instance:
        history = instance.history.all()[:8]
    return render(
        request,
        "studio/form.html",
        _ctx(
            request,
            title=("Modifier" if instance else "Nouveau") + f" {spec.singular}",
            form=form,
            spec=spec,
            object=instance,
            mode="edit" if instance else "create",
            history=history,
        ),
    )


@studio_gate()
def resource_delete(request, resource, pk):
    spec = get_resource(resource)
    if spec is None or not spec.can_delete:
        raise Http404()
    obj = get_object_or_404(spec.model, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, f"{spec.singular.capitalize()} supprimé.")
        return redirect("studio:list", resource=resource)
    return render(
        request,
        "studio/confirm_delete.html",
        _ctx(request, title=f"Supprimer {spec.singular}", spec=spec, object=obj),
    )


@studio_gate()
def message_list(request):
    queryset = ContactMessage.objects.all()
    query = request.GET.get("q", "").strip()
    if query:
        queryset = queryset.filter(
            Q(name__icontains=query)
            | Q(email__icontains=query)
            | Q(phone__icontains=query)
            | Q(subject__icontains=query)
            | Q(message__icontains=query)
        )
    if request.method == "POST":
        action = request.POST.get("action")
        ids = request.POST.getlist("ids")
        selected = ContactMessage.objects.filter(pk__in=ids)
        if action == "delete":
            selected.delete()
            messages.success(request, "Messages supprimés.")
        elif action == "read":
            selected.update(is_read=True)
            messages.success(request, "Marqués comme lus.")
        return redirect("studio:messages")
    page = Paginator(queryset, 12).get_page(request.GET.get("page"))
    return render(request, "studio/messages.html", _ctx(request, title="Messages", page=page, query=query))


@studio_gate()
def message_detail(request, pk):
    obj = get_object_or_404(ContactMessage, pk=pk)
    if not obj.is_read:
        obj.is_read = True
        obj.save(update_fields=["is_read"])
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Message supprimé.")
        return redirect("studio:messages")
    return render(request, "studio/message_detail.html", _ctx(request, title=obj.subject, object=obj))


@studio_gate()
def lock_list(request):
    if request.method == "POST":
        AccessLock.objects.filter(pk__in=request.POST.getlist("ids")).update(failures=0, locked_until=None)
        messages.success(request, "Adresses débloquées.")
        return redirect("studio:locks")
    locks = AccessLock.objects.all().order_by("-last_attempt")
    return render(request, "studio/locks.html", _ctx(request, title="Sécurité", locks=locks))
