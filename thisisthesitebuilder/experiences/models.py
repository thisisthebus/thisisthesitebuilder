import maya
from django.db import models
from thisisthebus.settings.constants import TIMEZONE_UTC_OFFSET
from thisisthesitebuilder.images.models import Image, Clip
from build.built_fundamentals import SUMMARIES, LOCATIONS, IMAGES, PLACES, INTERTWINED_MEDIA


class Era(models.Model):
    start = models.DateTimeField()
    end = models.DateTimeField()
    slug = models.SlugField()
    name = models.CharField(max_length=100)
    description = models.TextField()
    summary = models.TextField()

    def __init__(self, tags=None, sections=None, *args, **kwargs):
        self.sections = sections or []
        self.tags = tags or []
        self.sub_experiences = []
        self.images = []
        super(Era, self).__init__(*args, **kwargs)

    def __str__(self):
        return self.name

    def absorb_happenings(self):
        """
        Figure out everything that happened during this experience and populate it with the appropriate metadata.
        """

        self.all_images_with_location = []
        self.all_summaries_with_location = []

        self.apply_locations()
        self.apply_images()
        self.apply_summaries()
        # self.sort_data_by_location()

    def apply_locations(self):
        self.locations = {}
        for filename, locations_for_day in LOCATIONS.items():
            day = filename.rstrip('.yaml')
            for time, place in locations_for_day.items():
                try:
                    location_maya = maya.parse(day + "T" + time)
                except TypeError:
                    raise("Had trouble parsing date or time in %s" % filename)
                if self.start_maya <= location_maya <= self.end_maya:
                    # The dates match - now let's make sure that, if this is a top-level experience, that this place can be listed on it.
                    can_be_listed = not self.sub_experiences or PLACES[place].get("show_on_top_level_experience")
                    if can_be_listed:
                        # This location qualifies!  We'll make this a 2-tuple with the place as the first item and any dates as the second.
                        if not place in self.locations.keys():
                            self.locations[place] = {'place_meta': PLACES[place],
                                                              'datetimes': [], 'images': [], "summaries": []}
                        self.locations[place]['datetimes'].append(location_maya)

        # Now that we have the locations for this self, loop through them again to get start and end mayas.
        for location in self.locations.values():
            location['start'] = min(location['datetimes'])
            location['end'] = max(location['datetimes'])

        # OK, but now we want locations to be a sorted list.
        self.locations = sorted(self.locations.values(), key=lambda l: l['start'])

    def apply_images(self):
        pass

    def apply_summaries(self):
        pass


class Eras(list):
    """
    A collection of groups of Eras (probably Experiences) to be displayed or otherwise considered together.

    The canonical use-case is for pagination.
    """
    def __init__(self, page_name="", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.page_name = page_name
        self.next_group()

    def next_group(self):
        self.current_group = []
        self.append(self.current_group)

    def add_to_group(self, era):
        """
        Add era to the current group.
        """
        self.current_group.append(era)

    def output_filename_for_group(self, group):
        group



class Experience(Era):

    display = models.CharField(max_length=30)
    show_locations = models.BooleanField(default=True)
    show_dates = models.BooleanField(default=True)

    def apply_images(self):

        for day, image_list in INTERTWINED_MEDIA.items():
            for image in image_list:
                image_maya = maya.parse(day + "T" + image.time + TIMEZONE_UTC_OFFSET)
                if self.start_maya < image_maya < self.end_maya:
                    applied_to_sub = False
                    for sub_experience in self.sub_experiences:
                        for tag in sub_experience.tags:
                            if tag in image.tags:
                                sub_experience.images.append(image)
                                applied_to_sub = True
                    if not applied_to_sub:
                        self.images.append(image)

                    if self.display == "by-location":
                        # Loop through locations again, this time determining if this image goes with this location.
                        for location in self.locations:
                            if location['start'] < image_maya < location['end']:
                                location['images'].append(image)
                                self.all_images_with_location.append(image)

    def apply_summaries(self):
        # summaries
        self.summaries = {}
        for day, summary in SUMMARIES.items():
            summary_maya = maya.parse(day)
            if self.start_maya < summary_maya and summary_maya < self.end_maya:
                self.summaries[day] = summary

                # If we're doing by-location, list the summaries that way.
                if self.display == "by-location":
                    # Loop through locations again, this time determining if this image goes with this location.
                    for location in self.locations:
                        if location['start'] < summary_maya < location['end']:
                            location['summaries'].append(summary)
                            self.all_summaries_with_location.append(SUMMARIES)

    def media_count(self):
        image_count = 0
        clip_count = 0
        for e in self.sub_experiences:
            sub_image_count, sub_clip_count = e.media_count()
            image_count += sub_image_count
            clip_count += sub_clip_count

        for i in self.images:
            if i.__class__ == Image:
                image_count += 1
            if i.__class__ == Clip:
                clip_count += 1

        return image_count, clip_count
