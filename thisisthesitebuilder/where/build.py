import os

import yaml
from thisisthebus.settings.constants import DATA_DIR

from thisisthesitebuilder.where.models import Place, Location

PLACES_DIR = "%s/authored/places" % DATA_DIR


def process_locations(places):
    print("-------------  Processing Locations  -------------")
    locations_dir = "%s/authored/locations" % DATA_DIR
    locations_dir_listing = os.walk(locations_dir)
    location_files = list(locations_dir_listing)[0][2]

    locations = {}
    for location_file in location_files:
        location_filename = "%s/%s" % (locations_dir, location_file)
        day = location_file.rstrip(".yaml")
        locations[day] = {}
        with open(location_filename, 'r') as f:
            location_bytes = f.read()
            location_yaml = yaml.load(location_bytes)
            for time, location_meta in location_yaml.items():
                try:
                    location = Location(day, time, places[location_meta])
                except TypeError:
                    place = places[location_meta[0]]
                    significance = location_meta[1]
                    location = Location(day, time, place, significance)

                locations[day][time] = location

    for place in places.values():
        if not place.is_used_in_location:
            print("*** {} is not used as a location".format(place))

    print("Process {count} locations at {place_count} places.".format(count=len(locations), place_count=len(places)))

    return locations


def process_places(wait_at_end=False, force_update=False):
    print("-------------  Processing Places  -------------")
    print("Reading Places from %s" % PLACES_DIR)
    authored_places_dir = os.walk(PLACES_DIR)

    places = {}
    new_places = 0

    for yaml_file in list(authored_places_dir)[0][2]:
        place = Place.from_yaml(yaml_file)
        created = place.compile(force_update)
        if created:
            new_places += 1
        place_name = yaml_file.replace('.yaml', '')
        places[place_name] = place

    print("Processed %s new Places" % new_places)

    if wait_at_end:
        input()

    return places

