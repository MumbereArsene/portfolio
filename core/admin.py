from django import forms
from django.contrib import admin, messages
from django.utils.html import format_html
from .models import (
    AccessLock,
    Certificate,
    ContactMessage,
    Curriculum,
    Focus,
    Milestone,
    Profile,
    Project,
    SiteStat,
    Skill,
    SkillCategory,
    SkillProgress,
    Tag,
)
from .previews import PreviewError, attach_homepage_preview


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("display_name", "email", "location", "availability", "updated_at")
    fieldsets = (
        ("Identité publique", {"fields": ("display_name", "first_name", "last_name", "photo")}),
        ("Accroche", {"fields": ("headline", "tagline", "bio", "availability", "location")}),
        ("Contact & réseaux", {"fields": ("email", "phone", "github", "linkedin", "website")}),
    )

    def has_add_permission(self, request):
        return not Profile.objects.exists()


@admin.register(SiteStat)
class SiteStatAdmin(admin.ModelAdmin):
    list_display = ("label", "value", "suffix", "order")
    list_editable = ("value", "suffix", "order")


@admin.register(Focus)
class FocusAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "order")
    list_editable = ("order",)


class SkillInline(admin.TabularInline):
    model = Skill
    extra = 1
    fields = ("name", "level", "order")


class SkillProgressInline(admin.TabularInline):
    model = SkillProgress
    extra = 1
    fields = ("level", "recorded_at", "note")


@admin.register(SkillCategory)
class SkillCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [SkillInline]


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "level", "latest_delta", "updated_at", "order")
    list_filter = ("category",)
    list_editable = ("level", "order")
    inlines = [SkillProgressInline]
    search_fields = ("name",)

    @admin.display(description="Δ")
    def latest_delta(self, obj):
        delta = obj.latest_delta
        if not delta:
            return "—"
        return f"{delta:+d}"


@admin.register(SkillProgress)
class SkillProgressAdmin(admin.ModelAdmin):
    list_display = ("skill", "level", "recorded_at", "note")
    list_filter = ("skill__category",)
    search_fields = ("skill__name", "note")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name", "category_labels")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    class Form(forms.ModelForm):
        refresh_preview = forms.BooleanField(
            required=False,
            label="Capturer l’accueil depuis le lien",
            help_text="Enregistre une image de la page d’accueil du lien live.",
        )

        class Meta:
            model = Project
            fields = "__all__"

    form = Form
    list_display = ("cover_thumb", "title", "category", "year", "featured", "published", "order")
    list_filter = ("category", "featured", "published", "year", "cover_from_live")
    search_fields = ("title", "excerpt", "description", "live_url")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
    list_editable = ("featured", "published", "order")
    fieldsets = (
        ("Fiche", {"fields": ("title", "slug", "excerpt", "description", "cover")}),
        ("Classement", {"fields": ("category", "tags", "year", "role", "accent")}),
        (
            "Lien & aperçu",
            {
                "fields": ("live_url", "repo_url", "refresh_preview", "cover_from_live"),
                "description": "Colle le lien du site : l’accueil est capturé comme image du portfolio.",
            },
        ),
        ("Publication", {"fields": ("featured", "published", "order")}),
    )
    readonly_fields = ("cover_from_live",)

    @admin.display(description="aperçu")
    def cover_thumb(self, obj):
        if obj.cover:
            return format_html(
                '<img src="{}" alt="" style="height:42px;width:72px;object-fit:cover;border-radius:6px">',
                obj.cover.url,
            )
        return "—"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        should_capture = obj.live_url and (
            form.cleaned_data.get("refresh_preview") or not obj.cover
        )
        if not should_capture:
            return
        try:
            attach_homepage_preview(obj)
            self.message_user(request, "Aperçu de la page d’accueil enregistré.", messages.SUCCESS)
        except PreviewError as exc:
            self.message_user(
                request,
                f"Lien enregistré, mais l’aperçu n’a pas pu être capturé : {exc}",
                messages.WARNING,
            )


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "organization", "period", "order")
    list_filter = ("kind",)
    list_editable = ("order",)


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("title", "issuer", "kind", "issued_on", "published", "featured", "order")
    list_filter = ("kind", "published", "featured")
    search_fields = ("title", "issuer", "credential_id")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("published", "featured", "order")
    fieldsets = (
        ("Certificat", {"fields": ("title", "slug", "issuer", "kind", "issued_on", "description")}),
        ("Preuve", {"fields": ("file", "image", "credential_id", "credential_url", "course_url")}),
        ("Publication", {"fields": ("featured", "published", "order")}),
    )


@admin.register(Curriculum)
class CurriculumAdmin(admin.ModelAdmin):
    list_display = ("title", "language", "version", "is_primary", "published", "updated_at")
    list_filter = ("language", "published", "is_primary")
    list_editable = ("is_primary", "published")
    search_fields = ("title", "summary")
    fieldsets = (
        ("CV", {"fields": ("title", "language", "version", "summary", "file")}),
        ("Publication", {"fields": ("is_primary", "published", "order")}),
    )


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "subject", "created_at", "is_read")
    list_filter = ("is_read",)
    search_fields = ("name", "email", "phone", "subject", "message")
    readonly_fields = ("name", "email", "phone", "subject", "message", "created_at")
    list_editable = ("is_read",)


@admin.register(AccessLock)
class AccessLockAdmin(admin.ModelAdmin):
    list_display = ("ip_address", "failures", "locked_until", "last_attempt")
    actions = ("unlock_selected",)
    readonly_fields = ("ip_address", "failures", "locked_until", "last_attempt")

    @admin.action(description="Débloquer")
    def unlock_selected(self, request, queryset):
        queryset.update(failures=0, locked_until=None)
