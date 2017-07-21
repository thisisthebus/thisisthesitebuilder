import os

class Image(object):

    def __init__(self, caption, hash, slug, time, date, ext, orig, tags=None, *args, **kwargs):
        self.tags = tags or []
        self.caption = caption
        self.hash = hash
        self.slug = slug
        self.time = time
        self.date = date
        self.extension = ext
        self.orig = orig

    def __str__(self):
        return self.slug

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
        return "{}/{}".format(self.image_path, fn)

    def thumb_url(self):
        fn = self.filename()
        return "{}/thumbs/{}".format(self.image_path, fn)

    def full_file_path(self, subdir):
        try:
            full_path = self.image_file_path + "/"
            if subdir:
                full_path += subdir + "/"
            full_path += self.filename(subdir=="unchanged")
        except AttributeError:
            raise TypeError("{} does not have an image_file_path".format(self.slug))
        return full_path

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