import json
import re
import ssl
from html.parser import HTMLParser
from urllib.error import URLError
from urllib.parse import quote, urljoin, urlparse
from urllib.request import Request, urlopen

from django.core.files.base import ContentFile
from django.utils.text import slugify

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
TIMEOUT = 25


class PreviewError(Exception):
    pass


def _request(url):
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    context = ssl.create_default_context()
    with urlopen(req, timeout=TIMEOUT, context=context) as response:
        data = response.read()
        content_type = response.headers.get_content_type()
        final_url = response.geturl()
        return data, content_type, final_url


def _looks_like_image(data, content_type):
    if content_type.startswith("image/"):
        return True
    return data.startswith(b"\x89PNG") or data.startswith(b"\xff\xd8\xff") or data[:4] in {b"RIFF", b"GIF8"}


def _extension(data, content_type):
    if "png" in content_type or data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if "webp" in content_type or data[:4] == b"RIFF":
        return "webp"
    if "gif" in content_type:
        return "gif"
    return "jpg"


class _MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.image = ""

    def handle_starttag(self, tag, attrs):
        if tag != "meta" or self.image:
            return
        mapping = dict(attrs)
        prop = mapping.get("property", mapping.get("name", "")).lower()
        if prop in {"og:image", "og:image:url", "twitter:image", "twitter:image:src"}:
            self.image = mapping.get("content", "")


def extract_og_image(html, base_url):
    parser = _MetaParser()
    try:
        parser.feed(html)
    except Exception:
        pass
    if parser.image:
        return urljoin(base_url, parser.image)
    match = re.search(
        r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image)["\'][^>]+content=["\']([^"\']+)',
        html,
        re.I,
    )
    if match:
        return urljoin(base_url, match.group(1))
    return ""


def _download_image(url):
    data, content_type, _ = _request(url)
    if not _looks_like_image(data, content_type) or len(data) < 2000:
        raise PreviewError("Réponse sans image utilisable.")
    return data, _extension(data, content_type)


def _screenshot_urls(page_url):
    encoded = quote(page_url, safe=":/?&=%")
    return [
        f"https://image.thum.io/get/width/1400/crop/900/noanimate/{page_url}",
        f"https://api.microlink.io/?url={encoded}&screenshot=true&meta=false&embed=screenshot.url",
    ]


def capture_homepage_bytes(page_url):
    parsed = urlparse(page_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise PreviewError("Lien invalide.")

    last_error = "Capture impossible."
    for shot_url in _screenshot_urls(page_url):
        try:
            data, content_type, final_url = _request(shot_url)
            if content_type in {"application/json", "text/json"}:
                payload = json.loads(data.decode("utf-8"))
                shot = (
                    (payload.get("data") or {}).get("screenshot") or {}
                )
                shot_src = shot.get("url") if isinstance(shot, dict) else payload.get("url")
                if not shot_src:
                    continue
                return _download_image(shot_src)
            if _looks_like_image(data, content_type) and len(data) > 8000:
                return data, _extension(data, content_type)
        except (URLError, TimeoutError, PreviewError, OSError, ValueError) as exc:
            last_error = str(exc)
            continue

    try:
        html, content_type, final_url = _request(page_url)
        if "html" in content_type:
            og_image = extract_og_image(html.decode("utf-8", "ignore"), final_url)
            if og_image:
                return _download_image(og_image)
    except (URLError, TimeoutError, PreviewError, OSError, ValueError) as exc:
        last_error = str(exc)

    raise PreviewError(last_error)


def attach_homepage_preview(project):
    if not project.live_url:
        raise PreviewError("Aucun lien live.")
    data, ext = capture_homepage_bytes(project.live_url)
    filename = f"{slugify(project.slug or project.title)}-accueil.{ext}"
    project.cover.save(filename, ContentFile(data), save=False)
    project.cover_from_live = True
    project.save(update_fields=["cover", "cover_from_live", "updated_at"])
    return project.cover.name
