from __future__ import print_function

import os

import maya
import yaml
from thisisthebus.settings.constants import DATA_DIR

from thisisthesitebuilder.utils.questions import what_time, which_day
from thisisthesitebuilder.where.build import process_places


def new_location():
    process_places()
    print("-------------------------------------------")

    places_dir_listing = os.walk("%s/authored/places" % DATA_DIR)
    places = sorted(list(places_dir_listing)[0][2])

    place = None
    while not place:
        print("Which place?")
        for counter, place in enumerate(places):
            print("(%s) " % counter, place)
        try:
            place_int = int(input(""))
            place = places[place_int]
        except (ValueError, IndexError):
            continue

    print("Place meta: %s" % place)

    day = None

    while not day:
        day = which_day()

    time = None
    while not time:
        time = what_time()

    day_yaml_filename = "%s/authored/locations/%s.yaml" % (DATA_DIR, day)

    try:
        with open(day_yaml_filename, 'r') as f:
            day_locations = yaml.load(f)
    except FileNotFoundError:
        day_locations = {}

    day_locations[time] = place.replace(".yaml", "")

    with open(day_yaml_filename, 'w') as f:
        yaml.dump(day_locations, f, default_flow_style=False)


if __name__ == "__main__":
    new_location()