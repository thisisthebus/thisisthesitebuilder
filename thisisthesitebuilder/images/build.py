import os

from thisisthebus.settings.constants import DATA_DIR
import json
from collections import OrderedDict
from .models import Image

image_data_dir = "%s/compiled/images" % DATA_DIR


def process_images():
    print("Processing Images.")

    images_by_date = {}
    images_by_slug = {}
    images_by_hash = {}

    non_unique_hashes = []
    non_unique_slugs = []
    image_count = 0
    for image_metadata_file in os.listdir(image_data_dir):
        day = image_metadata_file.strip(".json")
        with open("%s/compiled/images/%s" % (DATA_DIR, image_metadata_file), 'r') as f:
            images_metadata_for_this_day = json.loads(f.read())
            day_images = []
            for image_metadata in images_metadata_for_this_day:
                image = Image(date=day, **image_metadata)
                image_count += 1

                day_images.append(image)
                image_hash = image_metadata['hash']
                image_slug = image_metadata['slug']

                if not image_hash in images_by_hash:
                    images_by_hash[image_hash] = image
                else:
                    non_unique_hashes.append(image_hash)

                if not image_slug in images_by_slug:
                    images_by_slug[image_slug] = image
                else:
                    non_unique_slugs.append(image_slug)

                images_by_date[day] = sorted(day_images, key=lambda i: i.time)
    print("Processed {count} images, with {slug_count} unique slugs.".format(count=image_count, slug_count=len(images_by_slug)))
    if non_unique_hashes:
        print("WARNING: non-unique hashes: ", non_unique_slugs)

    return OrderedDict(sorted(images_by_date.items(), key=lambda iotd: iotd[0])), images_by_hash, images_by_slug, non_unique_hashes, non_unique_slugs