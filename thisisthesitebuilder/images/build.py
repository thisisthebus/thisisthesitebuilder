import os


import json
from collections import OrderedDict
from .models import Image


class MultimediaCollection(object):

    def __init__(self, data_dir, multimedia_class):
        self.data_dir = data_dir
        self.MultimediaClass = multimedia_class

        self._by_date = {}
        self.by_slug = {}
        self.by_hash = {}

        self.non_unique_hashes = []
        self.non_unique_slugs = []
        self.count = 0

        self.walk_files()

    def __str__(self):
        return "{type} collection - {count}".format(type=self.MultimediaClass.__name__, count=self.count)

    def walk_files(self):
        for metadata_file in os.listdir(self.data_dir):
            day = metadata_file.strip(".json")
            with open("%s/%s" % (self.data_dir, metadata_file), 'r') as f:
                try:
                    metadata_for_this_day = json.loads(f.read())
                except json.decoder.JSONDecodeError as e:
                    error_message = "Problem with image metadata {file}: {message}".format(
                        file=metadata_file, message=e)
                    raise ValueError(error_message)
                day_images = []
                for metadata in metadata_for_this_day:
                    try:
                        media_object = self.MultimediaClass(date=day, **metadata)
                    except TypeError:
                        raise TypeError("Can't make a {media_type} from {metadata}".format(media_type=self.MultimediaClass, metadata=metadata))
                    self.count += 1

                    day_images.append(media_object)
                    file_hash = metadata['hash']
                    slug = metadata['slug']

                    if not file_hash in self.by_hash:
                        self.by_hash[file_hash] = media_object
                    else:
                        self.non_unique_hashes.append(file_hash)

                    if not slug in self.by_slug:
                        self.by_slug[slug] = media_object
                    else:
                        self.non_unique_slugs.append(slug)

                    self._by_date[day] = sorted(day_images, key=lambda i: i.time)

    def by_date(self):
        return OrderedDict(sorted(self._by_date.items(), key=lambda iotd: iotd[0]))

    def lookup_by_hash(self, hash):
        if not hash in self.non_unique_hashes:
            return self.by_hash[hash]
        else:
            raise ValueError("The hash %s is not unique." % hash)

    def lookup_by_slug(self, slug):
        if not slug in self.non_unique_slugs:
            return self.by_slug[slug]
        else:
            raise ValueError("The slug %s is not unique." % slug)


def intertwine(*media_collections):
    intertwined = {}
    dates = set()

    for media_collection in media_collections:
        dates.update(media_collection.by_date().keys())

    for day in dates:
        day_collection = []
        for media_collection in media_collections:
            if media_collection.by_date().get(day):
                day_collection.extend(media_collection.by_date()[day])

        day_collection.sort(key=lambda media_object: media_object.time)

        intertwined[day] = day_collection

    return OrderedDict(sorted(intertwined.items(), key=lambda collection: collection[0]))