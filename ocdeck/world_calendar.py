"""Local-date windows, priority and cross-year festival calendars."""

from datetime import date, timedelta
from functools import lru_cache
import holidays
from dateutil.easter import easter


# Actual dates, not substitute bank holidays. Curated global festival selection.
@lru_cache(maxsize=64)
def dates(year, country):
    result = [
        ("newyear", date(year, 1, 1), 90),
        ("valentine", date(year, 2, 14), 30),
        ("patrick", date(year, 3, 17), 30),
        ("earth", date(year, 4, 22), 30),
        ("july4", date(year, 7, 4), 80),
        ("halloween", date(year, 10, 31), 80),
        ("christmas", date(year, 12, 25), 100),
        ("easter", easter(year), 70),
    ]
    # US Thanksgiving is the fourth Thursday in November.
    first = date(year, 11, 1)
    result.append(("thanksgiving", first + timedelta(days=(3 - first.weekday()) % 7 + 21), 80))
    for nation, subdiv, matches in [
        ("IN", "UP", {"holi": "holi", "diwali": "diwali"}),
        ("CN", None, {"lunar": "chinese new year (spring festival)"}),
        ("IN", "UP", {"eid": "eid al-fitr"}),
    ]:
        calendar = holidays.country_holidays(nation, subdiv=subdiv, years=year, observed=False, language="en_US")
        for ident, text in matches.items():
            found = [day for day, name in calendar.items() if text in name.lower()]
            if found:
                result.append((ident, min(found), 70))
    from pyluach.dates import HebrewDate

    for hebrew_year in (year + 3760, year + 3761):
        event = HebrewDate(hebrew_year, 9, 25).to_greg().to_pydate()
        if event.year == year:
            result.append(("hanukkah", event, 70))
    # Canada celebrates Thanksgiving in October.
    if country == "CA":
        result = [entry for entry in result if entry[0] != "thanksgiving"]
        first = date(year, 10, 1)
        result.append(("thanksgiving", first + timedelta(days=(0 - first.weekday()) % 7 + 7), 80))
    return tuple(result)


def active_holiday(day, options, country=""):
    if not options["holidays"]:
        return None
    enabled = {s.strip() for s in options["holiday_ids"].split(",")}
    candidates = []
    for year in (day.year - 1, day.year, day.year + 1):
        entries = list(dates(year, country))
        if options["birthday"]:
            try:
                entries.append(("birthday", date.fromisoformat(f"{year}-{options['birthday']}"), 110))
            except ValueError:  # Leap-day birthdays stay on February 29.
                pass
        for ident, event, priority in entries:
            if ident not in enabled:
                continue
            before = max(
                options["before_days"],
                options["halloween_days"]
                if ident == "halloween"
                else options["christmas_days"]
                if ident == "christmas"
                else 0,
            )
            offset = (day - event).days
            after = max(options["after_days"], 7 if ident == "hanukkah" else 0)
            if -before <= offset <= after:
                candidates.append((offset == 0, priority, -abs(offset), ident))
    return max(candidates)[-1] if candidates else None


def season(day, south=False):
    index = (day.month % 12) // 3
    return ("winter", "spring", "summer", "autumn")[(index + (2 if south else 0)) % 4]


def quiet(hour, start, end):
    if start < 0 or start == end:
        return False
    return start <= hour < end if start < end else hour >= start or hour < end
