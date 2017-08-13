from django import template
register = template.Library()


def register_image_tags(image_instance_template_location, media_collection):

    @register.inclusion_tag(image_instance_template_location)
    def include_media(media_detail_dict=None, **media_details):
        # Silly workaround since we can't unpack args in a template.
        if media_detail_dict:
            media_details = media_detail_dict
        slug = media_details.get('slug')
        distinguisher = media_details.get('distinguisher')
        width = media_details.get('width')
        if distinguisher:
            media_object = media_collection.lookup_by_distinguisher(distinguisher)
        elif slug:
            media_object = media_collection.lookup_by_slug(slug)
        else:
            raise ValueError("Need either slug or distinguisher.")
        context = {'media_object': media_object, 'thumb_width': width, 'media_note': media_details.get('note')}

        return context