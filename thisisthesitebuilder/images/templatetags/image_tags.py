from django import template

register = template.Library()


def register_image_tags(image_instance_template_location):

    @register.inclusion_tag(image_instance_template_location)
    def include_image(date=None, slug=None, hash=None):
        if not slug and not hash:
            raise ValueError("Need either slug or hash.")
        return