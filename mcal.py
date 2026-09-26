"""
mcal.py - US stock market calendar (NYSE / Nasdaq): full-day holidays, 1:00 pm early closes, bond-market-only holidays,
trading days. Computed from the official rules, so it works for any year.
"""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")


def _nth(year, month, weekday, n):
    """n-th weekday (0=Mon) of a month; n=-1 -> last."""
    if n > 0:
        d = date(year, month, 1)
        d += timedelta(days=(weekday - d.weekday()) % 7)
        return d + timedelta(weeks=n - 1)
    d = date(year + (month == 12), month % 12 + 1, 1) - timedelta(days=1)
    return d - timedelta(days=(d.weekday() - weekday) % 7)


def easter(year):
    """Western Easter Sunday (anonymous Gregorian algorithm)."""
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l_) // 451
    month = (h + l_ - 7 * m + 114) // 31
    day = (h + l_ - 7 * m + 114) % 31 + 1
    return date(year, month, day)


def _observed(d):
    """Saturday -> Friday, Sunday -> Monday."""
    return d - timedelta(days=1) if d.weekday() == 5 else d + timedelta(days=1) if d.weekday() == 6 else d


# name_en, name_ar
NAMES = {"newyear": ("New Year's Day", "رأس السنة الميلادية"), "mlk": ("Martin Luther King Jr. Day", "يوم مارتن لوثر كينغ"),
         "presidents": ("Washington's Birthday (Presidents' Day)", "يوم الرؤساء"), "goodfriday": ("Good Friday", "الجمعة العظيمة"),
         "memorial": ("Memorial Day", "يوم الذكرى"), "juneteenth": ("Juneteenth", "يوم التحرر (جونتينث)"),
         "independence": ("Independence Day", "يوم الاستقلال"), "labor": ("Labor Day", "عيد العمال"),
         "thanksgiving": ("Thanksgiving Day", "عيد الشكر"), "christmas": ("Christmas Day", "عيد الميلاد"),
         "jul3": ("Day before Independence Day", "اليوم السابق ليوم الاستقلال"), "blackfriday": ("Day after Thanksgiving", "اليوم التالي لعيد الشكر"),
         "xmaseve": ("Christmas Eve", "ليلة عيد الميلاد"), "columbus": ("Columbus Day", "يوم كولومبوس"), "veterans": ("Veterans Day", "يوم المحاربين القدامى")}


def year_events(year):
    """[(date, key, kind)] kind: 'closed' (stocks closed all day), 'early' (stocks close 1:00 pm ET), 'bonds' (only the bond market closed)."""
    ev = []
    ny = date(year, 1, 1)
    if ny.weekday() != 5:                       # on a Saturday it is not moved to Friday Dec 31
        ev.append((_observed(ny), "newyear", "closed"))
    ev += [(_nth(year, 1, 0, 3), "mlk", "closed"), (_nth(year, 2, 0, 3), "presidents", "closed"),
           (easter(year) - timedelta(days=2), "goodfriday", "closed"), (_nth(year, 5, 0, -1), "memorial", "closed")]
    if year >= 2022:
        ev.append((_observed(date(year, 6, 19)), "juneteenth", "closed"))
    j4 = date(year, 7, 4)
    ev.append((_observed(j4), "independence", "closed"))
    if j4.weekday() in (1, 2, 3, 4):            # July 3 is a normal weekday -> 1 pm close
        ev.append((date(year, 7, 3), "jul3", "early"))
    ev.append((_nth(year, 9, 0, 1), "labor", "closed"))
    tg = _nth(year, 11, 3, 4)
    ev += [(tg, "thanksgiving", "closed"), (tg + timedelta(days=1), "blackfriday", "early")]
    xm = date(year, 12, 25)
    ev.append((_observed(xm), "christmas", "closed"))
    if xm.weekday() in (1, 2, 3, 4):            # Dec 24 is Mon-Thu -> 1 pm close
        ev.append((date(year, 12, 24), "xmaseve", "early"))
    ev.append((_nth(year, 10, 0, 2), "columbus", "bonds"))
    vd = date(year, 11, 11)
    if vd.weekday() != 5:
        ev.append((vd + timedelta(days=1) if vd.weekday() == 6 else vd, "veterans", "bonds"))
    return sorted(ev)


def closed_days(years):
    return {d for y in years for d, _, k in year_events(y) if k == "closed"}


def early_days(years):
    return {d for y in years for d, _, k in year_events(y) if k == "early"}


def today_et():
    return datetime.now(ET).date()


def day_status(d=None):
    """-> ('closed', key) | ('early', key) | ('weekend', None) | ('open', None)"""
    d = d or today_et()
    if d.weekday() >= 5:
        return "weekend", None
    for x, key, kind in year_events(d.year):
        if x == d and kind in ("closed", "early"):
            return kind, key
    return "open", None


def is_trading_day(d):
    return d.weekday() < 5 and d not in closed_days({d.year})


def trading_days(start, end):
    """Trading days between two dates (inclusive)."""
    closed = closed_days(range(start.year, end.year + 1))
    n, d = 0, start
    while d <= end:
        if d.weekday() < 5 and d not in closed:
            n += 1
        d += timedelta(days=1)
    return n


def next_trading_day(d):
    d += timedelta(days=1)
    while not is_trading_day(d):
        d += timedelta(days=1)
    return d


def prev_trading_day(d):
    d -= timedelta(days=1)
    while not is_trading_day(d):
        d -= timedelta(days=1)
    return d

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "7.2"
