from datetime import date

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from core.models import (
    TAG_CATEGORY_MAP,
    Certificate,
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


def placeholder_pdf(title, lines):
    def esc(text):
        return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    ops = ["BT /F1 18 Tf 50 750 Td", f"({esc(title)}) Tj", "/F1 11 Tf 0 -24 Td"]
    for line in lines:
        ops.append(f"({esc(line)}) Tj 0 -16 Td")
    ops.append("ET")
    stream = "\n".join(ops).encode("latin-1", "replace")
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n"
        b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n"
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources<< /Font<< /F1 5 0 R >> >> >>endobj\n"
        + f"4 0 obj<< /Length {len(stream)} >>stream\n".encode("ascii")
        + stream
        + b"\nendstream\nendobj\n"
        + b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n"
        + b"trailer<< /Root 1 0 R >>\n%%EOF\n"
    )


class Command(BaseCommand):
    help = "Charge le contenu de démonstration du portfolio."

    def handle(self, *args, **options):
        profile, _ = Profile.objects.update_or_create(
            pk=1,
            defaults={
                "display_name": "Mumbere Siviwe",
                "first_name": "Siviwe",
                "last_name": "Mumbere",
                "also_known_as": "Arsène",
                "headline": "Étudiant math-info, futur ingénieur data & deep learning",
                "tagline": "Je relie les maths, les données et Django pour construire des plateformes qui servent vraiment.",
                "bio": (
                    "Je suis étudiant en mathématiques et informatique. "
                    "Mon cap est clair : devenir ingénieur data, puis aller plus loin côté deep learning. "
                    "En parallèle, je développe avec Python et Django — assez pour livrer des plateformes réelles, "
                    "pas seulement des notebooks. J’utilise aussi le vibe coding pour prototyper vite, "
                    "itérer avec l’IA, et transformer une idée en produit utilisable."
                ),
                "location": "Ouvert aux stages et collaborations",
                "email": "arsene@example.com",
                "github": "https://github.com/",
                "linkedin": "https://linkedin.com/",
                "availability": "Disponible pour un stage data, deep learning ou Django",
            },
        )

        stats = [
            (0, "Axes", "04", ""),
            (1, "Projets", "06", ""),
            (2, "Certificats", "03", ""),
            (3, "CV", "02", ""),
        ]
        SiteStat.objects.all().delete()
        SiteStat.objects.bulk_create(
            [SiteStat(order=o, label=l, value=v, suffix=s) for o, l, v, s in stats]
        )

        focuses = [
            ("01", "Math-info", "Fondations : analyse, algèbre, proba, algo. C’est la grammaire de tout le reste."),
            ("02", "Ingénierie data", "Collecter, nettoyer, relier, servir. Des pipelines utiles, pas des slides."),
            ("03", "Deep learning", "Modèles, données, évaluation. Comprendre ce qui apprend, et pourquoi ça casse."),
            ("04", "Django & vibe", "Des plateformes livrées. Prototyper vite, structurer ensuite, garder le code lisible."),
        ]
        Focus.objects.all().delete()
        Focus.objects.bulk_create(
            [Focus(order=i, code=c, title=t, description=d) for i, (c, t, d) in enumerate(focuses)]
        )

        catalog = {
            "Mathématiques": [
                ("Analyse", 78),
                ("Algèbre linéaire", 82),
                ("Probabilités", 80),
                ("Statistiques", 76),
                ("Optimisation", 68),
            ],
            "Données": [
                ("Python", 85),
                ("Pandas", 78),
                ("SQL", 74),
                ("ETL / pipelines", 70),
                ("Visualisation", 72),
            ],
            "Deep learning": [
                ("PyTorch", 62),
                ("Réseaux de neurones", 65),
                ("Computer vision", 58),
                ("Évaluation de modèles", 64),
            ],
            "Développement": [
                ("Django", 80),
                ("HTML / CSS", 76),
                ("Git", 78),
                ("API REST", 68),
            ],
            "Vibe coding": [
                ("Prototypage IA", 84),
                ("Itération rapide", 86),
                ("Product thinking", 70),
            ],
        }
        Skill.objects.all().delete()
        SkillCategory.objects.all().delete()
        for i, (cat_name, skills) in enumerate(catalog.items()):
            category = SkillCategory.objects.create(name=cat_name, order=i)
            Skill.objects.bulk_create(
                [
                    Skill(category=category, name=name, level=level, order=j)
                    for j, (name, level) in enumerate(skills)
                ]
            )

        for skill in Skill.objects.all():
            start = max(skill.level - 14, 35)
            mid = max(skill.level - 6, start + 1)
            SkillProgress.objects.create(
                skill=skill, level=start, recorded_at=date(2025, 3, 12), note="Point de départ"
            )
            SkillProgress.objects.create(
                skill=skill, level=mid, recorded_at=date(2025, 11, 4), note="Progression"
            )
            SkillProgress.objects.create(
                skill=skill, level=skill.level, recorded_at=date(2026, 6, 18), note="Niveau actuel"
            )

        tags = {}
        for name, cats in TAG_CATEGORY_MAP.items():
            tag, _created = Tag.objects.get_or_create(name=name)
            if tag.categories != cats:
                tag.categories = cats
                tag.save(update_fields=["categories"])
            tags[name] = tag

        projects_data = [
            {
                "title": "ITIP Bumbu",
                "slug": "itip-bumbu",
                "excerpt": "Plateforme Django en production pour l’Institut technique de Bumbu : site public, bulletins, notes et examens.",
                "description": (
                    "ITIP Bumbu est une application Django de gestion scolaire, en ligne sur itipbumbu.com. "
                    "Elle couvre le site public de l’institut, les bulletins numériques, la saisie des notes, "
                    "l’organisation des examens, et les espaces parent / élève.\n\n"
                    "La plateforme sépare clairement les rôles : super admin, admin de module, direction, "
                    "secrétariat, enseignants, jury, parents et élèves. Les comptes parents sont créés "
                    "uniquement par l’administration — pas d’inscription publique.\n\n"
                    "Les portails internes sont installables en PWA. Côté infra : Docker sur Hetzner, "
                    "Nginx, Gunicorn, PostgreSQL, Redis et Celery pour la génération des PDF de bulletins, "
                    "devant Cloudflare. Un vrai produit livré, pas un prototype."
                ),
                "category": Project.Category.WEB,
                "role": "Conception, développement Django et mise en production",
                "year": 2026,
                "live_url": "https://itipbumbu.com",
                "accent": "#d4ff4a",
                "featured": True,
                "order": 0,
                "tags": ["Django", "Python", "PostgreSQL", "Docker", "Celery", "PWA"],
            },
            {
                "title": "Pipeline Orion",
                "excerpt": "Chaîne ETL Python pour nettoyer, joindre et exposer des jeux de données.",
                "description": (
                    "Orion prend des fichiers bruts, les normalise, détecte les trous, "
                    "et produit des tables prêtes à l’analyse. "
                    "J’ai travaillé les jointures, la qualité de données, et un petit rapport "
                    "d’anomalies. C’est le genre de projet qui me rapproche du métier d’ingénieur data : "
                    "rendre une donnée fiable avant de la rendre jolie."
                ),
                "category": Project.Category.DATA,
                "role": "Data engineering",
                "year": 2025,
                "accent": "#6ee7f9",
                "featured": True,
                "order": 1,
                "tags": ["Python", "Pandas", "ETL", "SQL"],
            },
            {
                "title": "Cortex Vision",
                "excerpt": "Premier laboratoire deep learning : classification d’images avec PyTorch.",
                "description": (
                    "Cortex Vision est un terrain d’entraînement. Dataset, architecture simple, "
                    "boucle d’apprentissage, métriques, erreurs. "
                    "L’objectif n’était pas le SOTA : c’était de comprendre ce qui se passe "
                    "quand un réseau apprend, où il se trompe, et comment on lit une matrice de confusion "
                    "sans se raconter d’histoires."
                ),
                "category": Project.Category.DEEP,
                "role": "Expérimentation deep learning",
                "year": 2025,
                "accent": "#ff7ad9",
                "featured": True,
                "order": 2,
                "tags": ["PyTorch", "Python", "Vision"],
            },
            {
                "title": "Lois Vivantes",
                "excerpt": "Exploration visuelle de lois de probabilité pour ancrer l’intuition mathématique.",
                "description": (
                    "Les maths restent abstraites tant qu’on ne les voit pas bouger. "
                    "Lois Vivantes simule des tirages, compare des distributions, "
                    "et montre l’effet d’un paramètre sur une densité. "
                    "Un pont entre le cours de proba et le travail sur les données réelles."
                ),
                "category": Project.Category.MATH,
                "role": "Maths appliquées & visualisation",
                "year": 2024,
                "accent": "#ffb020",
                "featured": False,
                "order": 3,
                "tags": ["Python", "Stats", "Pandas"],
            },
            {
                "title": "PulseDesk",
                "excerpt": "Dashboard Django pour suivre des indicateurs et des journaux d’activité.",
                "description": (
                    "PulseDesk agrège des métriques simples — volumes, statuts, tendances — "
                    "et les affiche dans une interface Django. "
                    "Je m’en sers comme bac à sable product : modèles, vues, filtres, "
                    "et une UI assez claire pour qu’un humain comprenne l’état du système en 10 secondes."
                ),
                "category": Project.Category.WEB,
                "role": "Full-stack Django",
                "year": 2025,
                "accent": "#7dffb3",
                "featured": True,
                "order": 4,
                "tags": ["Django", "Python", "REST", "CSS"],
            },
            {
                "title": "VibeForge",
                "excerpt": "Atelier de prototypes rapides : idées → plateformes, avec l’IA dans la boucle.",
                "description": (
                    "VibeForge n’est pas un seul produit. C’est ma méthode : "
                    "partir d’une intention, coder avec l’IA, recadrer, jeter ce qui ne tient pas, "
                    "et garder une base Django propre. "
                    "Plusieurs plateformes personnelles sont nées comme ça — vite d’abord, solides ensuite."
                ),
                "category": Project.Category.VIBE,
                "role": "Product & vibe coding",
                "year": 2026,
                "accent": "#d4ff4a",
                "featured": False,
                "order": 5,
                "tags": ["Vibe coding", "Django", "Python"],
            },
        ]

        Project.objects.all().delete()
        for data in projects_data:
            tag_list = data.pop("tags")
            project = Project.objects.create(**data, published=True)
            project.tags.set([tags[name] for name in tag_list])

        milestones = [
            (
                Milestone.Kind.EDUCATION,
                "Licence / parcours math-info",
                "Formation universitaire",
                "En cours",
                "Mathématiques et informatique en parallèle : rigueur d’un côté, systèmes de l’autre.",
            ),
            (
                Milestone.Kind.EXPERIENCE,
                "ITIP Bumbu — plateforme scolaire",
                "Institut technique de Bumbu",
                "2025 — 2026",
                "Site public, bulletins, notes, examens et espaces parent / élève. Django en production.",
            ),
            (
                Milestone.Kind.EXPERIENCE,
                "Laboratoire data & deep",
                "Projets d’étude",
                "2025 — aujourd’hui",
                "Pipelines, nettoyage, premiers modèles. Apprendre le métier en le pratiquant.",
            ),
            (
                Milestone.Kind.ACHIEVEMENT,
                "Vibe coding assumé",
                "Méthode de travail",
                "2025 — 2026",
                "Utiliser l’IA pour accélérer, pas pour remplacer le raisonnement. Livrer, puis durcir.",
            ),
        ]
        Milestone.objects.all().delete()
        Milestone.objects.bulk_create(
            [
                Milestone(order=i, kind=k, title=t, organization=o, period=p, description=d)
                for i, (k, t, o, p, d) in enumerate(milestones)
            ]
        )

        Certificate.objects.all().delete()
        certs = [
            {
                "title": "SQL pour l'analyse de données",
                "issuer": "Formation en ligne",
                "kind": Certificate.Kind.COURSE,
                "issued_on": date(2025, 5, 20),
                "description": "Requêtes, jointures, agrégations. Base pour le travail data.",
                "featured": True,
                "order": 0,
                "filename": "sql-analyse.pdf",
            },
            {
                "title": "Django : applications web",
                "issuer": "Pratique projet",
                "kind": Certificate.Kind.CERT,
                "issued_on": date(2025, 11, 8),
                "description": "Modèles, vues, admin, déploiement. Compétence utilisée sur ITIP Bumbu.",
                "featured": True,
                "order": 1,
                "filename": "django-web.pdf",
            },
            {
                "title": "Fondamentaux du deep learning",
                "issuer": "Cours / laboratoire",
                "kind": Certificate.Kind.COURSE,
                "issued_on": date(2026, 3, 2),
                "description": "Réseaux, loss, évaluation. Première couche avant les projets vision.",
                "featured": True,
                "order": 2,
                "filename": "deep-learning.pdf",
            },
        ]
        for data in certs:
            filename = data.pop("filename")
            cert = Certificate.objects.create(**data, published=True)
            cert.file.save(
                filename,
                ContentFile(placeholder_pdf(cert.title, [cert.issuer, cert.description])),
                save=True,
            )

        Curriculum.objects.all().delete()
        cv_data = [
            {
                "title": "CV — Data & Django",
                "language": "FR",
                "version": "2026.09",
                "summary": "Version orientée ingénierie data, Python et plateformes Django.",
                "is_primary": True,
                "order": 0,
                "filename": "cv-data-django.pdf",
            },
            {
                "title": "CV — parcours math-info",
                "language": "FR",
                "version": "2026.09",
                "summary": "Version académique : formation, projets et compétences mathématiques.",
                "is_primary": False,
                "order": 1,
                "filename": "cv-math-info.pdf",
            },
        ]
        for data in cv_data:
            filename = data.pop("filename")
            cv = Curriculum.objects.create(**data, published=True)
            cv.file.save(
                filename,
                ContentFile(
                    placeholder_pdf(
                        cv.title,
                        [cv.summary, "Remplace ce PDF depuis l'admin Django, section CV."],
                    )
                ),
                save=True,
            )

        self.stdout.write(self.style.SUCCESS("Contenu de démonstration chargé."))
