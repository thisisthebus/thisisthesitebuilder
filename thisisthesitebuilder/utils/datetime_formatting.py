

def month_day_maybe_year(maya_dt1, maya_dt2):
    if maya_dt2.epoch - maya_dt1.epoch > 60 * 60 * 24 * 7 * 45: # More than 40 weeks
        format = "%b %d %Y"
    else:
        format = "%b %d"

    return maya_dt1.datetime(to_timezone="America/New_York").strftime(format)