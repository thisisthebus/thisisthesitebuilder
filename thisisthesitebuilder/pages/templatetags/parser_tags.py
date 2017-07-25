from django import template
from thisisthesitebuilder.pages.parsers import parse_markdown_and_django_template

register = template.Library()


@register.simple_tag()
def parse_md_dj(blob):
    return parse_markdown_and_django_template(blob)