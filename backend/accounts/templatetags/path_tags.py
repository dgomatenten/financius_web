from django import template

register = template.Library()


@register.filter
def startswith(value: str, prefix: str) -> bool:
    return str(value).startswith(prefix)
