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
        self.locations = []
        for filename, locations_for_day in LOCATIONS.items():
            day = filename.rstrip('.yaml')
            for time, location in locations_for_day.items():
                try:
                    location_maya = maya.parse(day + "T" + time)
                except TypeError:
                    raise("Had trouble parsing date or time in %s" % filename)
                if self.start_maya <= location_maya <= self.end_maya:
                    # The dates match - now let's make sure that, if this is a top-level experience, that this place can be listed on it.
                    can_be_listed = not self.sub_experiences or location.place.show_on_top_level_experience
                    if can_be_listed:
                        self.add_location(location)



        # Now that we have the locations for this self, loop through them again to get start and end mayas.
        # for location in self.locations.values():
        #     location['start'] = min(location['datetimes'])
        #     location['end'] = max(location['datetimes'])

        # OK, but now we want locations to be a sorted list.
        self.locations = sorted(self.locations, key=lambda l: l.__str__())

    def add_location(self, location):
        self.locations.append(location)

    def find_intersecting(self, experiences):
        """
        Takes a list of experiences.
        Sets the attribute, intersecting, which is a list of experiences which start or end within this one.
        """
        self.intersection = []
        for experience in experiences:
            begins_within = self.start_maya < experience.start_maya < self.end_maya
            ends_within = self.start_maya < experience.end_maya < self.end_maya

            if begins_within or ends_within:
                self.intersection.append(experience)

    def places(self, reverse_order=False):
        locations = sorted(list(set(self.locations)), key=lambda l: l.__str__(), reverse=reverse_order)
        places = []
        for location in locations:
            if location.place not in places:
                places.append(location.place)
        return places

    def unique_locations_by_field(self, field, reverse_order=False):

        seen_values = []
        unique_values_and_locations = {}
        familiar_values_and_locations = {}

        for location in self.locations:
            place = location.place
            value = place.__dict__[field]

            if value in seen_values:
                places_with_this_value = familiar_values_and_locations.setdefault(value, [])
                seen_location = unique_values_and_locations.pop(value, None)

                if seen_location:
                    places_with_this_value.append(seen_location)

                places_with_this_value.append(location)
            else:
                unique_values_and_locations[value] = location
            seen_values.append(value)

        unique_place_locations = list(unique_values_and_locations.values())

        for value, location_list in familiar_values_and_locations.items():
            most_significant_location = max(location_list, key=lambda l: l.significance())
            unique_place_locations.append(most_significant_location)

        unique_place_locations = sorted(list(set(unique_place_locations)), key=lambda l: l.__str__(),
                           reverse=reverse_order)
        return unique_place_locations

    def unique_places_by_field(self, field):
        unique_place_locations = self.unique_locations_by_field(field)
        return [l.place for l in unique_place_locations]

    def unique_locations_by_big_name(self):
        unique_locations = self.unique_locations_by_field("big_name")
        return unique_locations

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
        place = self.index(group)
        if place == 0:
            return self.page_name
        else:
            return "{page_name}-page-{place}".format(page_name=self.page_name, place=place + 1)

    def output_filename_and_previous_group(self, group):
        place = self.index(group)
        if place == 0:
            return None, None
        else:
            previous_group = self[place - 1]
            return previous_group, self.output_filename_for_group(previous_group)

    def output_filename_and_next_group(self, group):
        place = self.index(group)
        try:
            next_group = self[place + 1]
            return next_group, self.output_filename_for_group(next_group)
        except IndexError:
            return None, None


class Experience(Era):

    display = models.CharField(max_length=30)
    show_locations = models.BooleanField(default=True)
    show_dates = models.BooleanField(default=True)

    def apply_images(self):

        for day, image_list in INTERTWINED_MEDIA.by_date().items():
            for image in image_list:
                image_maya = maya.parse(day + "T" + image.time + TIMEZONE_UTC_OFFSET)
                if self.start_maya < image_maya < self.end_maya:
                    image.is_used = True
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

    def add_location(self, location):
        super().add_location(location)
        if self not in location.used_in_experiences:
            location.used_in_experiences.append(self)
