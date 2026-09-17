from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import (
    Certificate,
    Curriculum,
    Focus,
    Milestone,
    Profile,
    Project,
    SiteStat,
    Skill,
    SkillCategory,
    Tag,
)


def polish(form):
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, forms.CheckboxInput):
            widget.attrs["class"] = "studio-check"
        elif isinstance(widget, (forms.SelectMultiple, forms.CheckboxSelectMultiple)):
            widget.attrs["class"] = "studio-multi"
        elif isinstance(widget, forms.ClearableFileInput):
            widget.attrs["class"] = "studio-file"
        elif isinstance(widget, forms.Textarea):
            widget.attrs.setdefault("rows", 6)
            widget.attrs["class"] = "studio-input"
        else:
            widget.attrs["class"] = "studio-input"
    return form


class StudioLoginForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "Identifiants incorrects.",
        "inactive": "Ce compte est inactif.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"placeholder": "Identifiant", "autocomplete": "username"})
        self.fields["password"].widget.attrs.update({"placeholder": "Mot de passe", "autocomplete": "current-password"})
        polish(self)
        self.fields["username"].label = "Identifiant"
        self.fields["password"].label = "Mot de passe"


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = (
            "display_name",
            "first_name",
            "last_name",
            "headline",
            "tagline",
            "bio",
            "location",
            "availability",
            "also_known_as",
            "email",
            "phone",
            "github",
            "linkedin",
            "website",
            "photo",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        polish(self)


class CategoryTagSelect(forms.CheckboxSelectMultiple):
    def __init__(self, *args, category_map=None, **kwargs):
        self.category_map = category_map or {}
        super().__init__(*args, **kwargs)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        try:
            pk = int(getattr(value, "value", value))
        except (TypeError, ValueError):
            pk = None
        option["attrs"]["data-categories"] = " ".join(self.category_map.get(pk, []))
        return option


class ProjectForm(forms.ModelForm):
    refresh_preview = forms.BooleanField(
        required=False,
        label="Capturer l’accueil depuis le lien live",
        help_text="Enregistre une image de la page d’accueil.",
    )

    class Meta:
        model = Project
        fields = (
            "title",
            "excerpt",
            "description",
            "category",
            "tags",
            "role",
            "year",
            "live_url",
            "repo_url",
            "cover",
            "accent",
            "featured",
            "published",
            "order",
        )
        widgets = {"tags": CategoryTagSelect}
        help_texts = {"tags": "Les tags affichés dépendent de la catégorie choisie."}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        mapping = {pk: cats or [] for pk, cats in Tag.objects.values_list("id", "categories")}
        self.fields["tags"].widget.category_map = mapping
        polish(self)
        self.fields["refresh_preview"].widget.attrs["class"] = "studio-check"


class CertificateForm(forms.ModelForm):
    class Meta:
        model = Certificate
        fields = (
            "title",
            "issuer",
            "kind",
            "issued_on",
            "credential_id",
            "credential_url",
            "course_url",
            "file",
            "image",
            "description",
            "featured",
            "published",
            "order",
        )
        widgets = {"issued_on": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        polish(self)


class CurriculumForm(forms.ModelForm):
    class Meta:
        model = Curriculum
        fields = ("title", "language", "version", "summary", "file", "is_primary", "published", "order")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        polish(self)


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ("category", "name", "level", "order")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        polish(self)
        self.fields["level"].widget.attrs.update({"min": 0, "max": 100})


class SkillCategoryForm(forms.ModelForm):
    class Meta:
        model = SkillCategory
        fields = ("name", "order")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        polish(self)


class MilestoneForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ("kind", "title", "organization", "period", "description", "order")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        polish(self)


class FocusForm(forms.ModelForm):
    class Meta:
        model = Focus
        fields = ("code", "title", "description", "order")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        polish(self)


class SiteStatForm(forms.ModelForm):
    class Meta:
        model = SiteStat
        fields = ("label", "value", "suffix", "order")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        polish(self)


class TagForm(forms.ModelForm):
    categories = forms.MultipleChoiceField(
        choices=Project.Category.choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Catégories de projet",
        help_text="Le tag n’apparaît que pour ces catégories.",
    )

    class Meta:
        model = Tag
        fields = ("name",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["categories"].initial = self.instance.categories or []
        polish(self)

    def save(self, commit=True):
        self.instance.categories = list(self.cleaned_data.get("categories") or [])
        return super().save(commit)
