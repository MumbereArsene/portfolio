from pathlib import Path

from django.http import FileResponse, Http404
from django.utils.text import slugify


def serve_pdf(file_field, *, download, fallback_name):
    if not file_field:
        raise Http404("Fichier indisponible.")
    try:
        handle = file_field.open("rb")
    except FileNotFoundError as exc:
        raise Http404("Fichier introuvable.") from exc
    name = Path(file_field.name).name or f"{slugify(fallback_name)}.pdf"
    if not name.lower().endswith(".pdf"):
        name = f"{name}.pdf"
    return FileResponse(handle, as_attachment=download, filename=name, content_type="application/pdf")
