import os


class Multimedia(object):

    def __init__(self, caption, hash, slug, time, date, ext, tags=None, *args, **kwargs):
        self.tags = tags or []
        self.caption = caption
        self.hash = hash
        self.slug = slug
        self.time = time
        self.date = date
        self.extension = ext

    def __str__(self):
        return self.slug

    @classmethod
    def set_storage_url_path(cls, storage_path):
        cls._storage_url_path = storage_path

    @classmethod
    def set_instance_template(cls, instance_template_name):
        cls.instance_template = instance_template_name

    def url_path(self):
        return self._storage_url_path + "/" + self.__class__.__name__

    def filename(self, orig=False):
        if orig:
            full_filename = self.orig
        else:
            full_filename = self.date

        if self.slug:
            full_filename += "__" + self.slug

        full_filename += "__{}.{}".format(self.hash, self.extension)
        return full_filename

    def full_url(self):
        fn = self.filename()
        return "{}/full/{}".format(self.url_path(), fn)

    def thumb_url(self):
        fn = self.filename()
        return "{}/thumbs/{}".format(self.url_path(), fn)

    def full_file_path(self, subdir):
        try:
            full_path = self.url_path() + "/"
            if subdir:
                full_path += subdir + "/"
            full_path += self.filename(subdir=="unchanged")
        except AttributeError:
            raise TypeError("{} does not have an image_file_path".format(self.slug))
        return full_path


class Image(Multimedia):

    def __init__(self, orig, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orig = orig

    def check_existence(self, subdir):
        full_path = self.full_file_path(subdir)
        exists = os.path.isfile(full_path)
        if not exists:
            print("Cannot find {}".format(full_path))
        return exists

    def check_thumb(self):
        return self.check_existence("thumbs")

    def check_full(self):
        return self.check_existence("")

    def check_unchanged(self):
        return self.check_existence("unchanged")

    def checksum_of_unchanged_file(self):
        unchanged_path = self.full_file_path("unchanged")
        with open(unchanged_path, "rb") as f:
            image_bytes = f.read(1024)
            image_checksum = hashlib.md5(image_bytes).hexdigest()[:8]
        return image_checksum


class Clip(Multimedia):

    def __init__(self, start, duration, *args, **kwargs):
        self.start = start
        self.duration = duration
        self.former_extension = kwargs.pop('ext')
        super().__init__(ext="webm", *args, **kwargs)

    def filename(self, orig=False):
        full_filename = self.date

        if self.slug:
            full_filename += "__" + self.slug

        full_filename += "__{}__{}-{}.{}".format(self.hash, self.start, self.duration, self.extension)
        return full_filename
