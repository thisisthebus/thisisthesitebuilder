import hashlib
import json

import maya
from build.built_fundamentals import SUMMARIES, LOCATIONS, INTERTWINED_MEDIA
from django.db import models
from thisisthebus.settings.constants import TIMEZONE_UTC_OFFSET

from thisisthesitebuilder.images.models import Image, Clip


class Era(models.Model):
    start = models.DateTimeField()
    end = models.DateTimeField()
    slug = models.SlugField()
    name = models.CharField(max_length=100)
    description = models.TextField()
    summary = models.TextField()

    def __init__(self, build_meta, tags=None, sections=None, persist=True, *args, **kwargs):
        self.build_meta = build_meta
        self.sections = sections or []
        self.persist = persist
        self.tags = tags or []
        self.sub_experiences = []

        self.images = []
        self._all_images_including_subs = []

        self.all_images_with_location = []
        self.all_summaries_with_location = []

        self.specific_locations = []
        self.all_locations = []

        self._has_absorbed_happenings = False

        super(Era, self).__init__(*args, **kwargs)

        self.start_maya = maya.MayaDT.from_datetime(self.start)
        self.end_maya = maya.MayaDT.from_datetime(self.end)

    def __str__(self):
        return self.name

    def absorb_happenings(self):
        """
        Figure out everything that happened during this experience and populate it with the appropriate metadata.
        """

        self.locations_checksum = self.apply_locations()
        self.multimedia_checksum = self.apply_images()
        self.summaries_checksum = self.apply_summaries()
        self.subs_checksum = hashlib.md5(str([str(s) for s in
                                              self.sub_experiences]).encode()).hexdigest()  # TODO: Check for updated lcoations, multimedia, and summaries in subs
        self.text_checksum = hashlib.md5(
            self.description.encode() + self.summary.encode()).hexdigest()
        self._has_absorbed_happenings = True

        if self.persist:
            try:
                json_meta_filename = "%s/compiled/experiences/%s.json" % (
                self.build_meta['data_dir'], self.slug)
                with open(json_meta_filename, "r") as f:
                    experience_meta_json = json.loads(f.read())

                self.locations_changed = self.locations_checksum != experience_meta_json[
                    'locations']
                self.multimedia_changed = self.multimedia_checksum != experience_meta_json[
                    'multimedia']
                self.summaries_changed = self.summaries_checksum != experience_meta_json[
                    'summaries']
                self.subs_changed = self.subs_checksum != experience_meta_json['subs']
                self.text_changed = self.text_checksum != experience_meta_json['text']

            except FileNotFoundError:
                # There is no JSON meta for this page yet.
                self.locations_changed = True
                self.multimedia_changed = True
                self.summaries_changed = True
                self.subs_changed = True
                self.text_changed = True

            if self.locations_changed or self.multimedia_changed or self.summaries_changed or self.subs_changed or self.text_changed:
                self.has_changed = True
                self.previous_meta = {
                    "locations": self.locations_checksum,
                    "multimedia": self.multimedia_checksum,
                    "summaries": self.summaries_checksum,
                    "subs": self.subs_checksum,
                    "text": self.text_checksum,
                    "datetime": self.build_meta['datetime'].iso8601(),
                    "build": self.build_meta['data_checksum'],
                    "what_changed": (
                    self.locations_changed, self.multimedia_changed, self.summaries_changed,
                    self.subs_changed, self.text_changed)
                }
                with open(json_meta_filename, "w") as f:
                    f.seek(0)
                    f.write(json.dumps(self.previous_meta, indent=2, sort_keys=True))
            else:
                self.has_changed = False
                self.previous_meta = experience_meta_json

    def last_updated(self):
        return maya.MayaDT.from_iso8601(self.previous_meta['datetime'])

    def apply_locations(self):
        for filename, locations_for_day in LOCATIONS.items():
            day = filename.rstrip('.yaml')
            for time, location in locations_for_day.items():
                try:
                    location_maya = maya.parse(day + "T" + time)
                except TypeError:
                    raise ("Had trouble parsing date or time in %s" % filename)
                if self.start_maya <= location_maya <= self.end_maya:
                    self.all_locations.append(location)
                    # The dates match - now let's make sure that, if this is a top-level experience, that this place can be listed on it.
                    can_be_listed = not self.sub_experiences or location.place.show_on_top_level_experience
                    if can_be_listed:
                        self.add_location(location)

        self.specific_locations.sort(key=lambda l: str(l))
        self.all_locations.sort(key=lambda l: str(l))

        distinguisher = str([str(l) for l in self.all_locations]).encode()
        return hashlib.md5(distinguisher).hexdigest()

    def add_location(self, location):
        self.specific_locations.append(location)

    def intersection(self):
        try:
            intersecting = self._intersection
        except AttributeError:
            raise TypeError("You need to find_intersecting experiences first.")

        return sorted(intersecting, key=lambda e: e.start_maya)

    def find_intersecting(self, experiences):
        """
        Takes a list of experiences.
        Sets the attribute, intersecting, which is a list of experiences which start or end within this one.
        """
        self._intersection = []
        for experience in experiences:
            begins_within = self.start_maya < experience.start_maya < self.end_maya
            ends_within = self.start_maya < experience.end_maya < self.end_maya

            if begins_within or ends_within:
                self._intersection.append(experience)

    def places(self, reverse_order=False):
        locations = sorted(list(set(self.all_locations)), key=lambda l: l.__str__(),
                           reverse=reverse_order)
        places = []
        for location in locations:
            if location.place not in places:
                places.append(location.place)
        return places

    def unique_locations_by_place(self):
        """
        Does *not* include sub-experiences.
        """
        seen_places = []
        unique_locations = []
        for location in self.specific_locations:
            if not location.place in seen_places:
                unique_locations.append(location)
            seen_places.append(location.place)
        return unique_locations

    def unique_locations_by_field(self, field, reverse_order=False):
        """
        *Includes* sub-experiences.
        """

        seen_values = []
        unique_values_and_locations = {}
        familiar_values_and_locations = {}

        for location in self.all_locations:
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

        unique_place_locations = sorted(list(set(unique_place_locations)),
                                        key=lambda l: l.__str__(),
                                        reverse=reverse_order)
        return unique_place_locations

    def unique_places_by_field(self, field):
        unique_place_locations = self.unique_locations_by_field(field)
        return [l.place for l in unique_place_locations]

    def unique_locations_by_big_name(self):
        unique_locations = self.unique_locations_by_field("big_name")
        return unique_locations

    def locations_from_intersecting_experiences(self):
        intersecting = self.intersection()
        experiences_and_places = []
        position = 1
        for experience in intersecting:
            experience_places = []
            experiences_and_places.append((experience, experience_places))
            locations = experience.unique_locations_by_big_name()

            for counter, location in enumerate(locations):
                must_clear = position - counter > 2 and 1 < len(locations) < 4
                if must_clear:
                    position = 1
                experience_places.append((location, position, must_clear))
                if position == 3:
                    position = 1
                else:
                    position += 1

        return experiences_and_places

    def apply_images(self):
        pass

    def apply_summaries(self):
        pass

    def pretty_name(self):
        return "{} ({} - {})".format(self.name, self.start_maya.slang_date(),
                                     self.end_maya.slang_date())

    def what_changed(self):
        locations_changed, multimedia_changed, summaries_changed, subs_changed, text_changed = self.previous_meta["what_changed"]
        things_that_changed = ""
        if locations_changed:
            things_that_changed += "locations, "
        if text_changed:
            things_that_changed += "text, "
        if multimedia_changed:
            things_that_changed += "images and/or clips, "
        return things_that_changed.rstrip(", ")


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
                    self._all_images_including_subs.append(image)
                    image.is_used = True
                    applied_to_sub = False
                    for sub_experience in self.sub_experiences:
                        for tag in sub_experience.tags:
                            if tag in image.tags:
                                sub_experience.images.append(image)
                                applied_to_sub = True
                    if not applied_to_sub:
                        self.images.append(image)

        return hashlib.md5(
            str([i.distinguisher() for i in self._all_images_including_subs]).encode()).hexdigest()

    def apply_summaries(self):
        # summaries
        self.summaries = {}
        for day, summary in SUMMARIES.items():
            summary_maya = maya.parse(day)
            if self.start_maya < summary_maya and summary_maya < self.end_maya:
                self.summaries[day] = summary

        return hashlib.md5(str(self.summaries).encode()).hexdigest()

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

    def url(self):
        return "/experiences/{}.html".format(self.slug)
