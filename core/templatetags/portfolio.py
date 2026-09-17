from django import template

register = template.Library()


@register.filter
def homepage_shot(url):
    if not url:
        return ""
    return f"https://image.thum.io/get/width/1400/crop/900/noanimate/{url}"
