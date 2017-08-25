import hashlib
import json
import maya
import yaml
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import get_template

from thisisthesitebuilder.pages.parsers import parse_markdown_and_django_template


class Page(object):
    def __init__(self, name, build_meta, template_name=None, root=False, active_context=None,
                 passive_context=None, compact=False, force_rebuild=False):
        self.name = name
        self.build_meta = build_meta
        self.template_name = template_name
        self.root = root

        self.context_is_built = False

        if root:
            self.full_name = "root!%s.html" % self.name
            self.output_filename = "%s.html" % self.name
        else:
            self.full_name = "%s.html" % self.name
            self.output_filename = "pages/%s.html" % self.name

        self.active_context = active_context or {}
        self.passive_context = passive_context or {}
        self.compact = compact
        self.force_rebuild = force_rebuild
        self.updated = False

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)

    def json_meta_filename(self):
        return (
            "%s/compiled/pages/%s.json" % (
                self.build_meta['data_dir'], self.full_name)).rstrip(
            ".html")

    def current_checksum(self):
        if not self.context_is_built:
            raise RuntimeError("You need to build context for this page first.")

        distinguisher = str(
            [(str(k), str(v)) for k, v in sorted(self.active_context.items())]
        ).encode()
        return hashlib.md5(distinguisher).hexdigest()

    def previous_checksum(self):
        try:
            checksum = self._previous_checksum
        except AttributeError:
            self.find_previous_checksum()
            checksum = self._previous_checksum
        return checksum

    def find_previous_meta(self):
        try:
            with open(self.json_meta_filename(), "r") as f:
                self._previous_meta = json.loads(f.read())
                return True
        except FileNotFoundError:
            # There is no JSON meta for this page yet.
            self._previous_meta = None
            return False

    def previous_meta(self, quiet=False):
        try:
            meta = self._previous_meta
        except AttributeError:
            meta_exists = self.find_previous_meta()
            if not meta_exists and not quiet:
                raise RuntimeError("{} has no meta file, but we need one.".format(str(self)))
            meta = self._previous_meta
        return meta

    def find_previous_checksum(self):
        previous_meta = self.previous_meta()
        if previous_meta is None:
            self._previous_checksum = None
        else:
            self._previous_checksum = previous_meta['page_checksum']

    def update_from_yaml(self, yaml_file):

        try:
            with open(yaml_file, "r") as f:
                page_yaml = yaml.load(f)

                self.active_context['compact'] = self.compact
                self.active_context['name'] = self.name

                self.active_context['title'] = self.active_context['page_title'] = page_yaml.pop(
                    'title',
                    self.name)

                body_content = page_yaml.pop('body_content', "")

                if not body_content:
                    try:
                        body_content_filename = (
                            "%s/authored/pages/%s" % (self.data_dir, self.full_page_name)).replace(
                            ".html",
                            "-body.md")
                        with open(body_content_filename, "r") as f:
                            body_content = f.read()
                    except FileNotFoundError:
                        pass

                self.active_context['body_content'] = parse_markdown_and_django_template(
                    body_content)

                self.active_context.update(page_yaml)


        except FileNotFoundError:
            # There is no yaml for this page. That's OK.
            pass

        self.context_is_built = True

    def render(self, force_rebuild=None):
        if force_rebuild is None:
            force_rebuild = self.force_rebuild

        if not force_rebuild and self.current_checksum() == self.previous_checksum():
            # No need to rebuild this page; it hasn't changed.
            self._last_updated = maya.MayaDT.from_iso8601(self.previous_meta()['last_update'])
        else:
            print("{} has changed.".format(self.name))

            if force_rebuild:
                last_meta = self.previous_meta(quiet=True)
                if last_meta:
                    last_update = maya.MayaDT.from_iso8601(last_meta['last_update'])
                else:
                    last_update = self.build_meta['datetime']
            else:
                last_update = self.build_meta['datetime']
            page_meta = {'page_checksum': self.current_checksum(),
                         'last_update': last_update.iso8601()}

            with open(self.json_meta_filename(), "w") as f:
                f.write(json.dumps(page_meta))

            self.active_context['build_time'] = last_update.datetime(to_timezone='US/Eastern',
                                                                     naive=True)
            self.active_context.update(self.passive_context)

            # Let's see if there's a special template for this page.
            try:
                template = get_template('page_specific/%s' % self.full_name)
            except TemplateDoesNotExist:
                template_name = self.template_name or self.active_context.get(
                    "template") or 'shared/generic-page.html'
                template = get_template(template_name)

            self.html = template.render(self.active_context)
            self.updated = True
            self._last_updated = last_update

    def last_updated(self):
        return self._last_updated

    def url(self):
        return self.output_filename

    def pretty_name(self):
        return self.active_context.get('title', self.name)