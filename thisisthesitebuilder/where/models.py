from __future__ import print_function

import hashlib
import json

import requests
import yaml
from thisisthebus.settings.constants import DATA_DIR, FRONTEND_APPS_DIR

from thisisthebus.settings.secrets import MAPBOX_ACCESS_KEY


class Place(object):

    thumb_width = 280
    thumb_height = 220

    def __init__(self, yaml_checksum, lat, lon, small_name, big_name, thumb_style, thumb_zoom,
                 use_both_names_for_slug, link_zoom, bearing=0, pitch=0,
                 show_on_top_level_experience=True, small_link=None, significance=0):
        self.yaml_checksum = yaml_checksum
        self.lat = lat
        self.lon = lon
        self.small_name = small_name
        self.big_name = big_name
        self.thumb_style = thumb_style
        self.thumb_zoom = thumb_zoom
        self.use_both_names_for_slug = use_both_names_for_slug
        self.link_zoom = link_zoom

        self.bearing = bearing
        self.pitch = pitch
        self.show_on_top_level_experience = show_on_top_level_experience
        self.small_link = small_link
        self.significance = 0

        self.is_used_in_location = False

    def __str__(self):
        return "{} - {}".format(self.small_name, self.big_name)

    @staticmethod
    def from_yaml(place_name):
        with open("%s/authored/places/%s" % (DATA_DIR, place_name), "r") as f:
            authored_place = yaml.load(f)
            f.seek(0)
            checksum = hashlib.md5(bytes(f.read(), encoding='utf-8')).hexdigest()

        place = Place(yaml_checksum=checksum, **authored_place)

        return place

    def slug(self):
        slug = self.small_name.replace(" ", "-").lower()

        if self.use_both_names_for_slug:
            slug += self.big_name.replace(" ", "-").replace(",", "").lower()

        return slug

    def filename(self):
        return "%s/compiled/places/%s" % (DATA_DIR, self.slug())

    def compiled_is_current(self):
        '''
        Looks at the compiled JSON version.  If checksum matches, returns the JSON representation.  Otherwise, False.
        '''
        try:
            with open("%s/compiled/places/%s" % (DATA_DIR, self.slug()), 'r') as f:
                json_representation = json.loads(f.read())
                checksum = json_representation.get('yaml_checksum')
                if checksum == self.yaml_checksum:
                    return json_representation
                else:
                    print("{big_name} - {small_name} is out of date.".format(**self.__dict__))
                    return False
        except FileNotFoundError:
            print("New Place: {small_name}. - {big_name}".format(**self.__dict__))
            return False

    def thumb_path(self):
        return '%s/places/img/%s' % (FRONTEND_APPS_DIR, self.thumb_filename)

    def compile(self, force_update=False):
        '''
        Grabs mapbox image, compiles uri, and writes JSON to data/compiled/places/{{place name}}
       '''
        if force_update:
            current_place_meta = False
        else:
            current_place_meta = self.compiled_is_current()
        if current_place_meta:
            self.thumb_filename = current_place_meta['thumb_filename']
            return False
        else:
            print("Compiling {small_name} - {big_name}".format(**self.__dict__))

        thumb_uri = "https://api.mapbox.com/styles/v1/mapbox/{thumb_style}/static/pin-s-bus({lon},{lat}/{lon},{lat},{thumb_zoom},{bearing},{pitch}/{width}x{height}?access_token={access_token}".format(
            width=self.thumb_width,
            height=self.thumb_height,
            access_token=MAPBOX_ACCESS_KEY,
            **self.__dict__
        )

        self.map_uri = "https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map={link_zoom}/{lat}/{lon}".format(
            **self.__dict__
        )

        response = requests.get(thumb_uri)

        if not response.status_code == 200:
            print(response.content)

        print("Content Type is %s" % response.headers['Content-Type'])
        self.thumb_filename = "%s.%s" % (self.slug(), response.headers['Content-Type'].split('/')[1])

        if self.yaml_checksum:
            self.yaml_checksum = self.yaml_checksum

        with open(self.thumb_path(), 'wb') as output:
            output.write(response.content)

        with open(self.filename(), 'w') as f:
            f.write(json.dumps(self.__dict__, sort_keys=True, indent=2))  # Actually, write place_meta

        return True


class Location(object):

    def __init__(self, day, time, place, significance=None):
        self.day = day
        self.time = time
        self.place = place

        self._significance = significance

        place.is_used_in_location = True
        self.used_in_experiences = []

    def __str__(self):
        return ("{}T{}: {}".format(self.day, self.time, self.place))

    def significance(self):
        if self._significance is None:
            return self.place.significance
        else:
            return self._significacne

    def most_significant_experience(self):
        if len(self.used_in_experiences) != 1:
            print("No implementation for most_significant_experience unless location has exactly 1 experience.")
        else:
            return self.used_in_experiences[0]