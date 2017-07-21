import maya
import yaml
from django.template.loader import get_template
from django.template.exceptions import TemplateDoesNotExist
import markdown
import hashlib
import json


class PageBuilder(object):

    def __init__(self, data_dir, frontend_dir):
        self.data_dir = data_dir
        self.frontend_dir = frontend_dir

    def build_page(self, page_name, **kwargs):
        return build_page(page_name, self.data_dir, self.frontend_dir, force_rebuild=True, **kwargs)


def parse_markdown_and_django_template(blob, context=None):
    context = context or {}
    from django.template import engines
    django_template_engine = engines['django']
    parsed_markdown = markdown.markdown(blob, extensions=['markdown.extensions.tables'])
    templated_content = django_template_engine.from_string(parsed_markdown)
    rendered_content = templated_content.render(context)
    return rendered_content


def build_page(page_name, data_dir, frontend_dir, template_name=None, root=False, context=None, slicey=False, force_rebuild=False):
    '''
    Takes a page name, checks to see if custom template or YAML files exist, writes HTML to frontend.
    '''
    context = context or {}
    context['slicey'] = slicey
    context['page_name'] = page_name
    if root:
        full_page_name = "root!%s.html" % page_name
        filename = "%s.html" % page_name
    else:
        full_page_name = "%s.html" % page_name
        filename = "pages/%s.html" % page_name

    try:
        yaml_filename = ("%s/authored/pages/%s" % (data_dir, full_page_name)).replace(".html", ".yaml")

        with open(yaml_filename, "r") as f:
            page_yaml = yaml.load(f)

        context['title'] = context['page_title'] = page_yaml.pop('title', page_name)

        body_content = page_yaml.pop('body_content', "")

        if not body_content:
            try:
                body_content_filename = ("%s/authored/pages/%s" % (data_dir, full_page_name)).replace(".html", "-body.md")
                with open(body_content_filename, "r") as f:
                    body_content = f.read()
            except FileNotFoundError:
                pass

        context['body_content'] = parse_markdown_and_django_template(body_content)

        context.update(page_yaml)

        page_checksum = hashlib.md5(json.dumps(context, sort_keys=True).encode()).hexdigest()

    except FileNotFoundError:
        # There is no yaml for this page. That's OK.
        pass
    else:

        try:
            json_meta_filename = ("%s/compiled/pages/%s.json" % (data_dir, full_page_name)).rstrip(".html")
            with open(json_meta_filename, "r") as f:
                page_meta_json = json.loads(f.read())

            previous_page_checksum = page_meta_json['page_checksum']

        except FileNotFoundError:
            # There is no JSON meta for this page yet.
            previous_page_checksum = None

        if not force_rebuild and page_checksum == previous_page_checksum:
            # No need to rebuild this page; it hasn't changed.
            return
        else:
            context['build_time'] = maya.now().datetime(to_timezone='US/Eastern', naive=True)
            page_meta = {'page_checksum': page_checksum}

        with open(json_meta_filename, "w") as f:
            f.write(json.dumps(page_meta))

    # Let's see if there's a special template for this page.
    try:
        template = get_template('page_specific/%s' % full_page_name)
    except TemplateDoesNotExist:
        template_name = template_name or context.get("template") or 'shared/generic-page.html'
        template = get_template(template_name)

    html = template.render(context)

    with open("%s/%s" % (frontend_dir, filename), "w+") as f:
        f.write(html)