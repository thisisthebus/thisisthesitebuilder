import datetime
import json
import shutil
import subprocess
import sys
import hashlib

from PIL import Image, ExifTags
from django.utils.text import slugify

MAX_SIZE = 1600.0
THUMB_SIZE = 400


def autorotate(image_file, orientation):
    if orientation == 3:
        image_file = image_file.rotate(180, expand=True)
    elif orientation == 6:
        image_file = image_file.rotate(270, expand=True)
    elif orientation == 8:
        image_file = image_file.rotate(90, expand=True)
    return image_file


def get_image_data_filename_for_day(day, data_dir):
    return "%s/compiled/images/%s.json" % (data_dir, day)


def get_clip_data_filename_for_day(day, data_dir):
    return "%s/compiled/clips/%s.json" % (data_dir, day)


def which_day(exif_date):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    print("Which day is this for?")
    if exif_date:
        print("1) The day it was taken (%s)" % exif_date)
    else:
        print("(This image is from an unknown date.)")
    print("2) Today (%s)" % today)
    print("3) Some other date")

    response = input("Enter 1-3: ")

    try:
        response = int(response)
    except ValueError:
        return

    if response == 1:
        if not exif_date:
            print("I told you - we don't know when the image was taken.  Try again.")
            day = None
        else:
            day = exif_date
    elif response == 2:
        day = today
    elif response == 3:
        day = str(input("Enter YYYY-MM-DD\n"))
    else:
        return
    return day


def what_time(exif_date):
    print("What time?")
    if exif_date:
        print("1) The time it was taken (%s)" % exif_date)
    else:
        print("(This image is from an unknown date.)")
    print("2) Midnight")
    print("3) Some other time")

    response = input("Enter 1-3: ")

    try:
        response = int(response)
    except ValueError:
        return

    if response == 1:
        if not exif_date:
            print("I told you - we don't know when the image was taken.  Try again.")
            time = None
        else:
            time = exif_date
    elif response == 2:
        time = "00:00:00"
    elif response == 3:
        time = str(input("Enter hh:mm:ss\n"))
    else:
        return
    return time

def ask_for_caption():
    return str(input("Enter a caption - say, 140 chars or so: "))

def ask_for_tags():
    tag_str = str(input("Tags, separated by comma: "))
    return tag_str.split(',')


def write_to_file(filename, payload):
    with open(filename, "w") as f:
        f.write(payload)
        print("writing %s:" % filename)
        print(payload)
        print("-----------------------------------")


def calculate_resize(w, h):
    full_resize_ratio = min(MAX_SIZE / w, MAX_SIZE / h)
    full_resize_ratio = min(full_resize_ratio, 1)

    thumb_resize_ratio = min(THUMB_SIZE / w, THUMB_SIZE / h)
    thumb_resize_ratio = min(thumb_resize_ratio, 1)

    full_size = h * full_resize_ratio, w * full_resize_ratio
    thumb_size = h * thumb_resize_ratio, w * thumb_resize_ratio
    return full_size, thumb_size


def parse_video(video_filename, data_dir, frontend_dir):
    result = subprocess.run(["ffprobe", "-print_format", "json", "-show_format", "-show_streams", video_filename], stdout=subprocess.PIPE)
    video_info = json.loads(result.stdout.decode('utf-8'))

    with open(video_filename, "rb") as f:
        f.seek(16384)
        video_bytes = f.read(2048)
        video_checksum = hashlib.md5(video_bytes).hexdigest()[:8]

    creation_dt = None

    try:
        creation_dt = video_info['format']['tags']['creation_time']
    except KeyError:
        try:
            creation_dt = video_info['streams'][0]['tags']['creation_time']
        except KeyError:
            pass

    try:
        day_video_was_taken, time_video_was_taken = creation_dt.split()
    except ValueError:
        day_video_was_taken = time_video_was_taken = None

    day = None
    while not day:
        day = which_day(day_video_was_taken)

    time = None
    while not time:
        time = what_time(time_video_was_taken)

    audio = None
    while audio not in ("Y", "N"):
        audio = str(input("Include Audio? (Y/N) "))

    start_time = str(input("At what second do you want to start?"))
    duration = str(input("How many seconds to capture?"))

    # Start our new meta dict by asking for a caption.
    new_clip = {'caption': ask_for_caption()}
    new_clip['tags'] = ask_for_tags()

    slug = slugify(new_clip['caption'][:30]) if new_clip['caption'] else ""
    file_detail = "{slug}__{hash}__{start_time}-{duration}".format(slug=slug, hash=video_checksum, start_time=start_time, duration=duration)

    extension = video_filename.split('.')[-1]

    full_filename = '/apps/multimedia/Clip/full/%s__%s.webm' % (day, file_detail)
    thumb_filename = '/apps/multimedia/Clip/thumbs/%s__%s.webm' % (day, file_detail)


    thumb_pass_1_args = [
        "ffmpeg", "-y", "-ss", start_time, "-t", duration, "-i", video_filename, "-maxrate", "80000", "-c:v",
        "libvpx-vp9", "-pass", "1", "-b:v", "1000K", "-threads", "1", "-speed", "4", "-tile-columns", "0",
        "-frame-parallel", "0", "-auto-alt-ref", "1", "-lag-in-frames", "25", "-g", "9999",
        "-aq-mode", "0", "-f", "webm", "-vf",
        "scale=256:-1", "/dev/null"]

    thumb_pass_2_args = [
        "ffmpeg", "-y", "-ss", start_time, "-t", duration, "-i", video_filename, "-maxrate", "80000", "-c:v",
        "libvpx-vp9", "-pass", "2", "-b:v", "1000K", "-threads", "1", "-speed", "0", "-tile-columns", "0",
        "-frame-parallel", "0", "-auto-alt-ref", "1", "-lag-in-frames", "25", "-g", "9999",
        "-aq-mode", "0", "-c:a", "libopus", "-b:a", "64k", "-f", "webm", "-vf",
        "scale=256:-1", frontend_dir + thumb_filename]

    full_pass_1_args = [
        "ffmpeg", "-y", "-ss", start_time, "-t", duration, "-i", video_filename, "-maxrate",
        "285000", "-c:v",
        "libvpx-vp9", "-pass", "1", "-b:v", "1000K", "-threads", "1", "-speed", "4",
        "-tile-columns", "0",
        "-frame-parallel", "0", "-auto-alt-ref", "1", "-lag-in-frames", "25", "-g", "9999",
        "-aq-mode", "0", "-f", "webm",
        "/dev/null"]

    full_pass_2_args = ["ffmpeg", "-y", "-ss", start_time, "-t", duration, "-i", video_filename, "-maxrate",
        "285000", "-c:v",
        "libvpx-vp9", "-pass", "2", "-b:v", "1000K", "-threads", "1", "-speed", "0",
        "-tile-columns", "0",
        "-frame-parallel", "0", "-auto-alt-ref", "1", "-lag-in-frames", "25", "-g", "9999",
        "-aq-mode", "0", "-c:a", "libopus", "-b:a", "64k", "-f",
        "webm",
        frontend_dir + full_filename]

    if audio == "N":
        for arg_list in (thumb_pass_1_args, thumb_pass_2_args, full_pass_1_args, full_pass_2_args):
            arg_list.insert(-1, "-an")


    thumb_pass_1_result = subprocess.run(thumb_pass_1_args, stdout=subprocess.PIPE)
    thumb_pass_2_result = subprocess.run(thumb_pass_2_args, stdout=subprocess.PIPE)
    full_pass_1_result = subprocess.run(full_pass_1_args, stdout=subprocess.PIPE)
    full_pass_2_result = subprocess.run(full_pass_2_args, stdout=subprocess.PIPE)

    new_clip['time'] = time
    new_clip['hash'] = video_checksum
    new_clip['slug'] = slug
    new_clip['ext'] = extension
    new_clip['start'] = start_time
    new_clip['duration'] = duration

    # Now to move the processed files to their appropriate locations.


    try:
        with open(get_clip_data_filename_for_day(day, data_dir), 'r') as f:
            this_day_meta = json.loads(f.read())
    except FileNotFoundError:
        this_day_meta = []

    this_day_meta.append(new_clip)

    write_to_file(filename=get_clip_data_filename_for_day(day, data_dir), payload=json.dumps(this_day_meta, indent=2))

    print("====================================\n")
    input("done!")

def parse_image(image_filename, data_dir, frontend_dir):

    image_filename = image_filename
    img = Image.open(image_filename)
    try:
        exif = {ExifTags.TAGS[k]: v for k, v in img._getexif().items() if k in ExifTags.TAGS}
        orientation = exif.get('Orientation')

        abridged_exif = {}
        for k in ('ApertureValue', 'DateTime', 'Flash', 'FocalLength', 'GPSInfo', 'Model', 'Orientation', 'ShutterSpeedValue'):
            abridged_exif[k] = exif.get(k)

        day_image_was_taken = abridged_exif['DateTime'].split()[0].replace(':', "-")
        time_image_was_taken = abridged_exif['DateTime'].split()[1]

    except AttributeError:
        # We apparently don't have exif data.
        orientation = None
        day_image_was_taken = None
        time_image_was_taken = None

    print("\n====================================")
    print("OK, let's add %s to our IOTD." % sys.argv[1])

    # Figure out what day this is an IOTD for.

    day = None

    while not day:
        day = which_day(day_image_was_taken)

    time = None
    while not time:
        time = what_time(time_image_was_taken)

    # Start our new meta dict by asking for a caption.
    new_iotd = {'caption': ask_for_caption()}
    new_iotd['tags'] = ask_for_tags()

    with open(image_filename, "rb") as f:
        image_bytes = f.read(1024)
        image_checksum = hashlib.md5(image_bytes).hexdigest()[:8]

    slug = slugify(new_iotd['caption'][:30]) if new_iotd['caption'] else ""
    file_detail = "{slug}__{hash}".format(slug=slug, hash=image_checksum)

    extension = image_filename.split('.')[-1]

    unchanged_filename = '/apps/multimedia/Image/unchanged/%s__%s.%s' % (img.filename.split('/')[-1], file_detail, extension)
    full_filename = '/apps/multimedia/Image/full/%s__%s.%s' % (day, file_detail, extension)
    thumb_filename = '/apps/multimedia/Image/thumbs/%s__%s.%s' % (day, file_detail, extension)

    new_iotd['time'] = time
    new_iotd['hash'] = image_checksum
    new_iotd['slug'] = slug
    new_iotd['orig'] = img.filename.split('/')[-1]
    new_iotd['ext'] = extension

    h = float(img.size[0])
    w = float(img.size[1])
    full_size, thumb_size = calculate_resize(w, h)

    try:
        with open(get_image_data_filename_for_day(day, data_dir), 'r') as f:
            this_day_meta = json.loads(f.read())
    except FileNotFoundError:
        this_day_meta = []

    this_day_meta.append(new_iotd)

    write_to_file(filename=get_image_data_filename_for_day(day, data_dir), payload=json.dumps(this_day_meta, indent=2))

    print("Saving original (%s, %s)" % (w, h))
    shutil.copyfile(image_filename, frontend_dir + unchanged_filename)

    print("full: resizing from (%s, %s) to %s" % (w, h, full_size))
    if orientation:
        img = autorotate(img, orientation)
    img.thumbnail(full_size, Image.ANTIALIAS)
    img.save(frontend_dir + full_filename, "JPEG", quality=60, optimize=True, progressive=True)
    print("------------------------------------")
    print("thumb: resizing from (%s, %s) to %s" % (w, h, thumb_size))
    thumb = Image.open(image_filename)
    if orientation:
        thumb = autorotate(thumb, orientation)
    thumb.thumbnail(thumb_size, Image.ANTIALIAS)
    thumb.save((frontend_dir + thumb_filename), "JPEG")
    print("====================================\n")
    input("done!")

