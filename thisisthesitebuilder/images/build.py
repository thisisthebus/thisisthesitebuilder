import os


import json
from collections import OrderedDict
from .models import Image


class MultimediaCollection(object):

    def __init__(self, data_dir=None, multimedia_class=None):
        self.data_dir = data_dir
        self.MultimediaClass = multimedia_class

        self._by_date = {}
        self.by_slug = {}
        self.by_distinguisher = {}
        self._as_list = []

        self.non_unique_distinguishers = []
        self.non_unique_slugs = []
        self.count = 0
        self.media_classes = set()

        if data_dir and multimedia_class:
            self.walk_files(data_dir, multimedia_class)

    def __str__(self):
        return "{types} collection - {count}".format(types=self.media_types(), count=self.count)

    def __iter__(self):
        return iter(sorted(self._as_list, key=lambda m: m.date_and_time()))

    def __next__(self):
        raise RuntimeError()

    @classmethod
    def intertwine(cls, *media_collections):
        intertwined = cls()

        for media_collection in media_collections:
            for media_object in media_collection:
                intertwined.include_media_object(media_object)

        return intertwined

    def media_types(self):
        return [cls.__name__ for cls in self.media_classes]

    def include_media_object(self, media_object):
        self._as_list.append(media_object)
        day_media_objects = self._by_date.setdefault(media_object.date, [])

        day_media_objects.append(media_object)
        distinguisher = media_object.distinguisher()
        slug = media_object.slug()

        if not distinguisher in self.by_distinguisher:
            self.by_distinguisher[distinguisher] = media_object
        else:
            self.non_unique_distinguishers.append(distinguisher)

        if not slug in self.by_slug:
            self.by_slug[slug] = media_object
        else:
            self.non_unique_slugs.append(slug)

        day_media_objects.sort(key=lambda i: i.time)

    def walk_files(self, data_dir, multimedia_class):
        self.media_classes.add(multimedia_class)
        for metadata_file in os.listdir(data_dir):
            day = metadata_file.strip(".json")
            with open("%s/%s" % (self.data_dir, metadata_file), 'r') as f:
                # Read the file and make sure it's valid JSON.
                try:
                    metadata_for_this_day = json.loads(f.read())
                except json.decoder.JSONDecodeError as e:
                    error_message = "Problem with media_objects metadata {file}: {message}".format(
                        file=metadata_file, message=e)
                    raise ValueError(error_message)
                # Populate a list for the media objects for this day.

                for metadata in metadata_for_this_day:
                    try:
                        media_object = self.MultimediaClass(date=day, **metadata)
                    except TypeError:
                        raise TypeError("Can't make a {media_type} from {metadata}".format(media_type=self.MultimediaClass, metadata=metadata))

                    self.include_media_object(media_object)

        print("Processed {} {} objects from {}".format(len(self._as_list), multimedia_class.__name__, data_dir))

    def by_date(self):
        return OrderedDict(sorted(self._by_date.items(), key=lambda iotd: iotd[0]))

    def lookup_by_distinguisher(self, distinguisher):
        if not hash in self.non_unique_distinguishers:
            return self.by_distinguisher[distinguisher]
        else:
            raise ValueError("The distinguisher %s is not unique." % hash)

    def lookup_by_slug(self, slug):
        if not slug in self.non_unique_slugs:
            return self.by_slug[slug]
        else:
            raise ValueError("The slug %s is not unique." % slug)
