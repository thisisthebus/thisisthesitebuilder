import markdown


def parse_markdown_and_django_template(blob, context=None):
    context = context or {}
    from django.template import engines
    django_template_engine = engines['django']
    parsed_markdown = markdown.markdown(blob, extensions=['markdown.extensions.tables'])
    templated_content = django_template_engine.from_string(parsed_markdown)
    rendered_content = templated_content.render(context)
    return rendered_content
