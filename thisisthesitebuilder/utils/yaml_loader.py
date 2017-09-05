import yaml
from collections import OrderedDict

from thisisthesitebuilder.pages.parsers import parse_markdown_and_django_template


def yaml_ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    class OrderedLoader(Loader):
        pass
    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)


def md_field_from_file(data_dir, subdir, content_filename, suffix):
    try:
        content_full_path = (
            "{}/authored/{}/{}{}.md".format(data_dir, subdir, content_filename, suffix))
        with open(content_full_path, "r") as f:
            content = f.read()
    except FileNotFoundError:
        return

    return parse_markdown_and_django_template(content)