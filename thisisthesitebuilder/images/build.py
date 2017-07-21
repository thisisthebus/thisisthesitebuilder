import os

from thisisthebus.settings.constants import DATA_DIR
import json
from collections import OrderedDict
from .models import Image

image_data_dir = "%s/compiled/images" % DATA_DIR


def process_images():
    print("Processing Images.")

    iotds = {}
    for image_metadata_file in os.listdir(image_data_dir):
        day = image_metadata_file.strip(".json")
        with open("%s/compiled/images/%s" % (DATA_DIR, image_metadata_file), 'r') as f:
            images_metadata_for_this_day = json.loads(f.read())
            day_images = []
            for image_metadata in images_metadata_for_this_day:
                day_images.append(Image(date=day, **image_metadata))
            iotds[day] = sorted(day_images, key=lambda i: i.time)

    return OrderedDict(sorted(iotds.items(), key=lambda iotd: iotd[0]))