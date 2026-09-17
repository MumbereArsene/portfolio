from dataclasses import dataclass, field

from .models import (
    Certificate,
    Curriculum,
    Focus,
    Milestone,
    Project,
    SiteStat,
    Skill,
    SkillCategory,
    Tag,
)
from .studio_forms import (
    CertificateForm,
    CurriculumForm,
    FocusForm,
    MilestoneForm,
    ProjectForm,
    SiteStatForm,
    SkillCategoryForm,
    SkillForm,
    TagForm,
)


@dataclass(frozen=True)
class Resource:
    key: str
    model: type
    form_class: type
    title: str
    singular: str
    columns: tuple
    search_fields: tuple = field(default_factory=tuple)
    can_create: bool = True
    can_delete: bool = True
    icon: str = "grid"


CATALOG = {
    "projets": Resource(
        key="projets",
        model=Project,
        form_class=ProjectForm,
        title="Projets",
        singular="projet",
        columns=(
            ("cover", "Aperçu", "image"),
            ("title", "Titre", "text"),
            ("category", "Catégorie", "choice"),
            ("year", "Année", "text"),
            ("published", "Publié", "bool"),
            ("featured", "Avant", "bool"),
        ),
        search_fields=("title", "excerpt", "description", "live_url"),
        icon="layers",
    ),
    "certificats": Resource(
        key="certificats",
        model=Certificate,
        form_class=CertificateForm,
        title="Certificats",
        singular="certificat",
        columns=(
            ("title", "Titre", "text"),
            ("issuer", "Organisme", "text"),
            ("issued_on", "Date", "date"),
            ("published", "Publié", "bool"),
        ),
        search_fields=("title", "issuer", "credential_id", "credential_url", "course_url"),
        icon="award",
    ),
    "cv": Resource(
        key="cv",
        model=Curriculum,
        form_class=CurriculumForm,
        title="CV",
        singular="CV",
        columns=(
            ("title", "Titre", "text"),
            ("language", "Langue", "text"),
            ("version", "Version", "text"),
            ("is_primary", "Principal", "bool"),
            ("published", "Publié", "bool"),
        ),
        search_fields=("title", "summary", "language"),
        icon="file",
    ),
    "competences": Resource(
        key="competences",
        model=Skill,
        form_class=SkillForm,
        title="Compétences",
        singular="compétence",
        columns=(
            ("name", "Nom", "text"),
            ("category", "Catégorie", "text"),
            ("level", "Niveau", "percent"),
            ("updated_at", "Maj", "date"),
        ),
        search_fields=("name", "category__name"),
        icon="activity",
    ),
    "categories": Resource(
        key="categories",
        model=SkillCategory,
        form_class=SkillCategoryForm,
        title="Catégories",
        singular="catégorie",
        columns=(("name", "Nom", "text"), ("order", "Ordre", "text")),
        search_fields=("name",),
        icon="folder",
    ),
    "parcours": Resource(
        key="parcours",
        model=Milestone,
        form_class=MilestoneForm,
        title="Parcours",
        singular="étape",
        columns=(
            ("title", "Titre", "text"),
            ("kind", "Type", "choice"),
            ("organization", "Organisation", "text"),
            ("period", "Période", "text"),
        ),
        search_fields=("title", "organization", "description"),
        icon="map",
    ),
    "axes": Resource(
        key="axes",
        model=Focus,
        form_class=FocusForm,
        title="Axes",
        singular="axe",
        columns=(("code", "Code", "text"), ("title", "Titre", "text"), ("order", "Ordre", "text")),
        search_fields=("title", "description", "code"),
        icon="compass",
    ),
    "stats": Resource(
        key="stats",
        model=SiteStat,
        form_class=SiteStatForm,
        title="Statistiques",
        singular="statistique",
        columns=(
            ("label", "Libellé", "text"),
            ("value", "Valeur", "text"),
            ("suffix", "Suffixe", "text"),
            ("order", "Ordre", "text"),
        ),
        search_fields=("label", "value"),
        icon="hash",
    ),
    "tags": Resource(
        key="tags",
        model=Tag,
        form_class=TagForm,
        title="Tags",
        singular="tag",
        columns=(("name", "Nom", "text"), ("category_labels", "Catégories", "text")),
        search_fields=("name",),
        icon="tag",
    ),
}


def get_resource(key):
    return CATALOG.get(key)
