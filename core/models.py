from datetime import date

from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

PDF_VALIDATOR = FileExtensionValidator(["pdf"])


class Profile(models.Model):
    display_name = models.CharField("nom affiché", max_length=80)
    first_name = models.CharField("prénom", max_length=60)
    last_name = models.CharField("nom", max_length=60, blank=True)
    headline = models.CharField("accroche", max_length=180)
    tagline = models.CharField("sous-titre", max_length=240, blank=True)
    bio = models.TextField("biographie")
    location = models.CharField("localisation", max_length=120, blank=True)
    email = models.EmailField("email")
    phone = models.CharField("téléphone", max_length=40, blank=True)
    github = models.URLField("GitHub", blank=True)
    linkedin = models.URLField("LinkedIn", blank=True)
    website = models.URLField("site web", blank=True)
    availability = models.CharField("disponibilité", max_length=160, blank=True)
    also_known_as = models.CharField(
        "aussi connu comme",
        max_length=80,
        blank=True,
        default="Arsène",
        help_text="Nom indexé pour Google, ex. Arsène.",
    )
    photo = models.ImageField("photo", upload_to="profile/", blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "profil"
        verbose_name_plural = "profil"

    def __str__(self):
        return self.display_name

    @property
    def full_name(self):
        return " ".join(part for part in [self.first_name, self.last_name] if part)


class SiteStat(models.Model):
    label = models.CharField("libellé", max_length=80)
    value = models.CharField("valeur", max_length=20)
    suffix = models.CharField("suffixe", max_length=12, blank=True)
    order = models.PositiveSmallIntegerField("ordre", default=0)

    class Meta:
        ordering = ["order"]
        verbose_name = "statistique"
        verbose_name_plural = "statistiques"

    def __str__(self):
        return f"{self.label}: {self.value}{self.suffix}"


class Focus(models.Model):
    code = models.CharField("code", max_length=8)
    title = models.CharField("titre", max_length=80)
    description = models.TextField("description")
    order = models.PositiveSmallIntegerField("ordre", default=0)

    class Meta:
        ordering = ["order"]
        verbose_name = "axe"
        verbose_name_plural = "axes"

    def __str__(self):
        return self.title


class SkillCategory(models.Model):
    name = models.CharField("nom", max_length=80)
    slug = models.SlugField(unique=True, blank=True)
    order = models.PositiveSmallIntegerField("ordre", default=0)

    class Meta:
        ordering = ["order"]
        verbose_name = "catégorie de compétence"
        verbose_name_plural = "catégories de compétences"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Skill(models.Model):
    category = models.ForeignKey(
        SkillCategory, on_delete=models.CASCADE, related_name="skills", verbose_name="catégorie"
    )
    name = models.CharField("nom", max_length=80)
    level = models.PositiveSmallIntegerField("niveau actuel", default=70, help_text="0 à 100 — augmente-le dans l’admin au fil du temps")
    order = models.PositiveSmallIntegerField("ordre", default=0)
    updated_at = models.DateTimeField("dernière mise à jour", auto_now=True)

    class Meta:
        ordering = ["category__order", "order", "name"]
        verbose_name = "compétence"
        verbose_name_plural = "compétences"

    def save(self, *args, **kwargs):
        creating = self.pk is None
        previous_level = None
        if not creating:
            previous_level = Skill.objects.filter(pk=self.pk).values_list("level", flat=True).first()
        super().save(*args, **kwargs)
        if creating:
            SkillProgress.objects.create(skill=self, level=self.level, note="Niveau initial")
        elif previous_level is not None and previous_level != self.level:
            delta = self.level - previous_level
            SkillProgress.objects.create(
                skill=self,
                level=self.level,
                note=f"{previous_level}% → {self.level}% ({delta:+d})",
            )

    def __str__(self):
        return self.name

    @property
    def latest_delta(self):
        entries = list(self.history.all()[:2])
        if len(entries) < 2:
            return 0
        return entries[0].level - entries[1].level


class SkillProgress(models.Model):
    skill = models.ForeignKey(
        Skill, on_delete=models.CASCADE, related_name="history", verbose_name="compétence"
    )
    level = models.PositiveSmallIntegerField("niveau")
    recorded_at = models.DateField("date", default=date.today)
    note = models.CharField("note", max_length=160, blank=True)

    class Meta:
        ordering = ["-recorded_at", "-id"]
        verbose_name = "évolution de compétence"
        verbose_name_plural = "historique des compétences"

    def __str__(self):
        return f"{self.skill.name} · {self.level}% · {self.recorded_at}"


TAG_CATEGORY_MAP = {
    "CSS": ["web", "vibe"],
    "Celery": ["web"],
    "Django": ["web", "vibe"],
    "Docker": ["web", "data", "deep"],
    "ETL": ["data"],
    "PWA": ["web", "vibe"],
    "Pandas": ["data", "deep", "math"],
    "PostgreSQL": ["web", "data"],
    "PyTorch": ["deep"],
    "Python": ["data", "deep", "web", "math", "vibe"],
    "REST": ["web", "data"],
    "SQL": ["data", "web", "math"],
    "SQLite": ["web", "data"],
    "Stats": ["data", "deep", "math"],
    "Vibe coding": ["vibe"],
    "Vision": ["deep"],
}


class Tag(models.Model):
    name = models.CharField("nom", max_length=40, unique=True)
    categories = models.JSONField(
        "catégories projet",
        default=list,
        blank=True,
        help_text="Le tag n’est proposé que pour ces catégories de projet.",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "tag"
        verbose_name_plural = "tags"

    def __str__(self):
        return self.name

    @property
    def category_labels(self):
        labels = dict(Project.Category.choices)
        return ", ".join(labels.get(key, key) for key in (self.categories or []))


class Project(models.Model):
    class Category(models.TextChoices):
        DATA = "data", "Ingénierie data"
        DEEP = "deep", "Deep learning"
        WEB = "web", "Plateforme Django"
        MATH = "math", "Math & info"
        VIBE = "vibe", "Vibe coding"

    title = models.CharField("titre", max_length=140)
    slug = models.SlugField(unique=True, blank=True)
    excerpt = models.CharField("extrait", max_length=240)
    description = models.TextField("description")
    category = models.CharField("catégorie", max_length=12, choices=Category.choices)
    tags = models.ManyToManyField(Tag, blank=True, related_name="projects")
    role = models.CharField("rôle", max_length=120, blank=True)
    year = models.PositiveSmallIntegerField("année")
    live_url = models.URLField(
        "lien live",
        blank=True,
        help_text="Si tu colles l’URL, le portfolio capture la page d’accueil comme image.",
    )
    repo_url = models.URLField("dépôt", blank=True)
    cover = models.ImageField("couverture", upload_to="projects/", blank=True)
    cover_from_live = models.BooleanField("aperçu capturé depuis le lien", default=False)
    accent = models.CharField("couleur d'accent", max_length=7, default="#d4ff4a")
    featured = models.BooleanField("mis en avant", default=False)
    published = models.BooleanField("publié", default=True)
    order = models.PositiveSmallIntegerField("ordre", default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "-year", "-created_at"]
        verbose_name = "projet"
        verbose_name_plural = "projets"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("core:project_detail", args=[self.slug])


class Milestone(models.Model):
    class Kind(models.TextChoices):
        EDUCATION = "education", "Formation"
        EXPERIENCE = "experience", "Expérience"
        ACHIEVEMENT = "achievement", "Repère"

    kind = models.CharField("type", max_length=20, choices=Kind.choices)
    title = models.CharField("titre", max_length=140)
    organization = models.CharField("organisation", max_length=140, blank=True)
    period = models.CharField("période", max_length=80)
    description = models.TextField("description", blank=True)
    order = models.PositiveSmallIntegerField("ordre", default=0)

    class Meta:
        ordering = ["order"]
        verbose_name = "étape"
        verbose_name_plural = "parcours"

    def __str__(self):
        return self.title


class Certificate(models.Model):
    class Kind(models.TextChoices):
        CERT = "cert", "Certificat"
        DIPLOMA = "diploma", "Diplôme"
        COURSE = "course", "Formation"
        BADGE = "badge", "Badge"

    title = models.CharField("titre", max_length=160)
    slug = models.SlugField(unique=True, blank=True)
    issuer = models.CharField("organisme", max_length=140)
    kind = models.CharField("type", max_length=12, choices=Kind.choices, default=Kind.CERT)
    issued_on = models.DateField("obtenu le")
    credential_id = models.CharField("identifiant", max_length=80, blank=True)
    credential_url = models.URLField(
        "lien du certificat",
        blank=True,
        help_text="URL du certificat (vérification, badge, PDF en ligne…).",
    )
    course_url = models.URLField(
        "lien de la formation",
        blank=True,
        help_text="Si la formation était en ligne, colle ici le lien du cours.",
    )
    file = models.FileField(
        "fichier PDF",
        upload_to="certificates/",
        blank=True,
        validators=[PDF_VALIDATOR],
    )
    image = models.ImageField("visuel", upload_to="certificates/images/", blank=True)
    description = models.TextField("description", blank=True)
    published = models.BooleanField("publié", default=True)
    featured = models.BooleanField("mis en avant", default=False)
    order = models.PositiveSmallIntegerField("ordre", default=0)

    class Meta:
        ordering = ["order", "-issued_on"]
        verbose_name = "certificat"
        verbose_name_plural = "certificats"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("core:certificate_detail", args=[self.slug])

    @property
    def can_view(self):
        return bool(self.file) or bool(self.credential_url) or bool(self.course_url) or bool(self.image)


class Curriculum(models.Model):
    title = models.CharField("titre", max_length=140)
    language = models.CharField("langue", max_length=8, default="FR")
    version = models.CharField("version", max_length=40, blank=True)
    summary = models.TextField("résumé", blank=True)
    file = models.FileField(
        "fichier PDF",
        upload_to="cv/",
        blank=True,
        validators=[PDF_VALIDATOR],
    )
    published = models.BooleanField("publié", default=True)
    is_primary = models.BooleanField("CV principal", default=False)
    order = models.PositiveSmallIntegerField("ordre", default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_primary", "order", "-updated_at"]
        verbose_name = "CV"
        verbose_name_plural = "CV"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_primary:
            Curriculum.objects.exclude(pk=self.pk).filter(is_primary=True).update(is_primary=False)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("core:cv_detail", args=[self.pk])


class ContactMessage(models.Model):
    name = models.CharField("nom", max_length=120)
    email = models.EmailField("email")
    phone = models.CharField(
        "WhatsApp",
        max_length=40,
        blank=True,
        help_text="Numéro avec indicatif, ex. 243812345678.",
    )
    subject = models.CharField("sujet", max_length=160)
    message = models.TextField("message")
    created_at = models.DateTimeField("reçu le", auto_now_add=True)
    is_read = models.BooleanField("lu", default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "message"
        verbose_name_plural = "messages"

    def __str__(self):
        return f"{self.name} — {self.subject}"

    @property
    def whatsapp_url(self):
        digits = "".join(char for char in (self.phone or "") if char.isdigit())
        if len(digits) < 8:
            return ""
        return f"https://wa.me/{digits}"

    @property
    def mailto_url(self):
        from urllib.parse import quote

        return f"mailto:{self.email}?subject={quote('Re: ' + self.subject)}"


class AccessLock(models.Model):
    ip_address = models.GenericIPAddressField("adresse IP", unique=True)
    failures = models.PositiveSmallIntegerField("échecs", default=0)
    locked_until = models.DateTimeField("bloqué jusqu’à", null=True, blank=True)
    last_attempt = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "verrou d’accès"
        verbose_name_plural = "verrous d’accès"

    def __str__(self):
        return self.ip_address

    def is_locked(self):
        from django.utils import timezone

        return bool(self.locked_until and self.locked_until > timezone.now())
