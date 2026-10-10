"""
mcal_sa.py - Saudi Exchange (Tadawul) calendar: trading days Sunday to Thursday, the market's own holidays (Founding Day,
the two Eids, National Day), the session hours (Asia/Riyadh). Same functions as mcal.py, so code that takes a calendar works
with either market.

The Eid holidays follow the Hijri calendar, so their dates come from the exchange's announcements (2024-2026); the 2027 ones
are estimates from the expected Hijri dates (marked 'approx') until the exchange announces them.
"""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Riyadh")
ET = TZ                                   # the name mcal.py uses for its own time zone
WEEKEND = (4, 5)                          # Friday, Saturday (Python: Monday = 0)
PRE_OPEN, OPEN, CLOSE, AUCTION_END, LAST_END = 570, 600, 900, 910, 920     # minutes: 9:30 opening auction, 10:00-15:00 market,
#                                         15:00-15:10 closing auction, 15:10-15:20 trade at last

NAMES = {"founding": ("Founding Day", "يوم التأسيس"), "fitr": ("Eid Al-Fitr holiday", "إجازة عيد الفطر"),
         "adha": ("Eid Al-Adha holiday", "إجازة عيد الأضحى"), "national": ("Saudi National Day", "اليوم الوطني"),
         "fitr_approx": ("Eid Al-Fitr holiday (expected)", "إجازة عيد الفطر (متوقعة)"),
         "adha_approx": ("Eid Al-Adha holiday (expected)", "إجازة عيد الأضحى (متوقعة)")}


def _span(a, b):
    d, out = a, []
    while d <= b:
        out.append(d)
        d += timedelta(days=1)
    return out


# (first closed day, last closed day, key): weekends inside a span are closed anyway
_HOLIDAYS = [
    (date(2024, 2, 22), date(2024, 2, 22), "founding"),
    (date(2024, 4, 7), date(2024, 4, 14), "fitr"),
    (date(2024, 6, 13), date(2024, 6, 22), "adha"),
    (date(2024, 9, 23), date(2024, 9, 23), "national"),
    (date(2025, 2, 23), date(2025, 2, 23), "founding"),
    (date(2025, 3, 30), date(2025, 4, 2), "fitr"),
    (date(2025, 6, 5), date(2025, 6, 10), "adha"),
    (date(2025, 9, 23), date(2025, 9, 23), "national"),
    (date(2026, 2, 22), date(2026, 2, 22), "founding"),
    (date(2026, 3, 17), date(2026, 3, 23), "fitr"),            # trading stopped after Mon 16 Mar, back Tue 24 Mar
    (date(2026, 5, 24), date(2026, 5, 28), "adha"),            # after Thu 21 May, back Sun 31 May
    (date(2026, 9, 23), date(2026, 9, 23), "national"),
    (date(2027, 2, 22), date(2027, 2, 22), "founding"),
    (date(2027, 3, 7), date(2027, 3, 11), "fitr_approx"),
    (date(2027, 5, 16), date(2027, 5, 20), "adha_approx"),
    (date(2027, 9, 23), date(2027, 9, 23), "national"),
]


def _fixed(year):
    """Founding Day (22 Feb) and National Day (23 Sep) for a year without an announced list: a Friday moves to the Thursday
    before, a Saturday to the Sunday after."""
    out = []
    for m, dd, key in ((2, 22, "founding"), (9, 23, "national")):
        d = date(year, m, dd)
        if d.weekday() == 4:
            d -= timedelta(days=1)
        elif d.weekday() == 5:
            d += timedelta(days=1)
        out.append((d, key))
    return out


def year_events(year):
    """[(date, key, 'closed')] the trading days the market is closed in a year (weekends left out)."""
    spans = [x for x in _HOLIDAYS if x[0].year == year or x[1].year == year]
    ev = []
    if spans:
        for a, b, key in spans:
            ev += [(d, key, "closed") for d in _span(a, b) if d.weekday() not in WEEKEND and d.year == year]
    else:
        ev = [(d, key, "closed") for d, key in _fixed(year)]
    return sorted(set(ev))


def spans(year):
    """[(first day, last day, key, trading days closed)] the market's holidays of a year, each Eid as one span."""
    sp = [x for x in _HOLIDAYS if x[0].year == year or x[1].year == year]
    if not sp:
        sp = [(d, d, key) for d, key in _fixed(year)]
    return sorted((a, b, key, sum(1 for d in _span(a, b) if d.weekday() not in WEEKEND)) for a, b, key in sp)


def closed_days(years):
    return {d for y in years for d, _, _ in year_events(y)}


def early_days(years):
    return set()


def now():
    return datetime.now(TZ)


def today_et():
    """Today in Riyadh (mcal.py's name, so either calendar answers the same call)."""
    return now().date()


today = today_et


def day_status(d=None):
    """-> ('closed', key) | ('weekend', None) | ('open', None)"""
    d = d or today_et()
    if d.weekday() in WEEKEND:
        return "weekend", None
    for x, key, _ in year_events(d.year):
        if x == d:
            return "closed", key
    return "open", None


def is_trading_day(d):
    return d.weekday() not in WEEKEND and d not in closed_days({d.year})


def trading_days(start, end):
    closed = closed_days(range(start.year, end.year + 1))
    n, d = 0, start
    while d <= end:
        if d.weekday() not in WEEKEND and d not in closed:
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


def close_min(d=None):
    return CLOSE


# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "22.4.1"
