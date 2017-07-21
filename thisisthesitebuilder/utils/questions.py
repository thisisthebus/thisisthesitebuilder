import datetime


def today_or_another_day():

    today = datetime.datetime.now().strftime("%Y-%m-%d")
    print("Which day in this location?")
    print("1) Today (%s)" % today)
    print("2) Some other date")

    response = input("Enter 1-2: ")

    try:
        response = int(response)
    except ValueError:
        return

    if response == 1:
        day = today
    elif response == 2:
        day = str(input("Enter YYYY-MM-DD\n"))
    else:
        return
    return day


def which_day():
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    print("Which day?")

    print("1) Today (%s)" % today)
    print("2) Some other date")

    response = input("Enter 1-2: ")

    try:
        response = int(response)
    except ValueError:
        return

    if response == 1:
        day = today
    elif response == 2:
        day = str(input("Enter YYYY-MM-DD\n"))
    else:
        return
    return day


def what_time():
    print("What time?")
    print("1) Midnight")
    print("2) Some other time")

    response = input("Enter 1-2: ")

    try:
        response = int(response)
    except ValueError:
        return

    if response == 1:
        time = "00:00:00"
    elif response == 2:
        time = str(input("Enter hh:mm:ss\n"))
    else:
        return
    return time