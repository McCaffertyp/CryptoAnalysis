from datetime import datetime
from dateutil.relativedelta import relativedelta


def adjust_year_and_format_datetime(date: datetime, years_adjust: int):
    year = (date - relativedelta(years=years_adjust)).year
    month = date.month
    day = date.day
    hour = date.hour
    minute = date.minute
    second = date.second

    if month < 10:
        month = "0{0}".format(month)
    if day < 10:
        day = "0{0}".format(day)
    if hour < 10:
        hour = "0{0}".format(hour)
    if minute < 10:
        minute = "0{0}".format(minute)
    if second < 10:
        second = "0{0}".format(second)

    return "{0}-{1}-{2}T{3}:{4}:{5}".format(year, month, day, hour, minute, second)


def adjust_hours_and_format_datetime(date_str: str, hours_adjust: int):
    date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    year = date.year
    month = date.month
    day = date.day
    hour = int(date.hour) + hours_adjust
    minute = date.minute
    second = date.second

    if month < 10:
        month = "0{0}".format(month)
    if day < 10:
        day = "0{0}".format(day)
    if hour < 10:
        hour = "0{0}".format(hour)
    if minute < 10:
        minute = "0{0}".format(minute)
    if second < 10:
        second = "0{0}".format(second)

    return "{0}-{1}-{2}T{3}:{4}:{5}".format(year, month, day, hour, minute, second)


def log(tag: str, message):
    print("{0} [LOG]/{1}: {2}".format(datetime.now(), tag, message))
