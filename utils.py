import random
from datetime import datetime
from dateutil.relativedelta import relativedelta


def now() -> datetime:
    return datetime.now()


def adjust_year_and_format_datetime(date: datetime, years_adjust: int) -> str:
    year = (date - relativedelta(years=years_adjust)).year
    month = date.month
    day = date.day
    hour = date.hour
    minute = date.minute
    second = date.second

    return format_date(year, month, day, hour, minute, second)


def adjust_months_and_format_datetime(date: datetime, months_adjust: int) -> str:
    year = (date - relativedelta(months=months_adjust)).year
    month = (date - relativedelta(months=months_adjust)).month
    day = date.day
    hour = date.hour
    minute = date.minute
    second = date.second

    return format_date(year, month, day, hour, minute, second)


def adjust_hours_and_format_datetime(date_str: str, hours_adjust: int, forward: bool = True) -> str:
    date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    year = date.year
    month = date.month
    day = (date + relativedelta(hours=hours_adjust)).day
    if not forward:
        day = (date - relativedelta(hours=hours_adjust)).day
    hour = (date + relativedelta(hours=hours_adjust)).hour
    if not forward:
        hour = (date - relativedelta(hours=hours_adjust)).hour
    minute = date.minute
    second = date.second

    return format_date(year, month, day, hour, minute, second)


def format_date(year, month, day, hour, minute, second) -> str:
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

    return "{0}-{1}-{2} {3}:{4}:{5}".format(year, month, day, hour, minute, second)


def get_random_number(low: int, high: int, include_high: bool = True) -> int:
    if include_high:
        return random.randint(low, high)
    else:
        return random.randint(low, (high - 1))


def sort_dict(d: dict, reverse: bool = False) -> dict:
    sorted_dict = dict()
    sorted_keys = sorted(d.keys(), reverse=reverse)
    for key in sorted_keys:
        sorted_dict[key] = d[key]
    return sorted_dict


def log(tag: str, message):
    print("{0} [LOG]/{1}: {2}".format(datetime.now(), tag, message))
