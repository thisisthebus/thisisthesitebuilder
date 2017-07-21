from django import template
from build.built_fundamentals import lookup_image_by_slug, lookup_image_by_hash
register = template.Library()


def register_image_tags(image_instance_template_location):

    @register.inclusion_tag(image_instance_template_location)
    def include_image(image_detail_dict=None, **image_details):
        # Silly workaround since we can't unpack args in a template.
        if image_detail_dict:
            image_details = image_detail_dict
        slug = image_details.get('slug')
        hash = image_details.get('hash')
        width = image_details.get('width')
        if hash:
            return {'iotd': lookup_image_by_hash(hash), 'thumb_width': width}
        elif slug:
            return {'iotd': lookup_image_by_slug(slug), 'thumb_width': width}
        else:
            raise ValueError("Need either slug or hash.")