"""
warm.py - Data kept ready in the background, so a visitor never waits for it (the home page's news reading, stories, movers,
mood, indicators and heat map). Each piece is computed once for every visitor and kept in this server process; when it gets
old, the next visitor still gets it at once while a fresh one is made in the background. A piece nobody has asked for yet is
started at once and waited for; several pieces asked for together are made side by side. While visitors come (a piece asked
for in the last two hours), a quiet thread keeps every such piece fresh, so even the first visitor after a quiet spell gets
fresh data at once.
"""
import sys
import threading
import time

BUILD = "23.4.62"

# kept on sys, so a reload of this module (a new version of the site) keeps what is ready
_STATE = sys.__dict__.setdefault("_tura_warm", {"store": {}, "busy": {}, "lock": threading.Lock(), "events": {}})
_STATE.setdefault("jobs", {})                    # key -> [fn, ttl, last time a visitor wanted it]
_STATE.setdefault("failed", {})                  # key -> when making it last failed (not tried again for its ttl)
_STATE.setdefault("gate", threading.BoundedSemaphore(2))   # pieces are made two at a time: the server has two cores and one Python
KEEP = 2 * 3600                                  # a piece nobody has wanted for this long is no longer kept fresh


def _want(key, fn, ttl, now=None):
    with _STATE["lock"]:
        _STATE["jobs"][key] = [fn, ttl, now or time.time()]
    _loop_start()


def _loop_start():
    if _STATE.get("loop"):
        return
    _STATE["loop"] = True

    def loop():
        while True:
            time.sleep(45)
            now = time.time()
            with _STATE["lock"]:
                jobs = [(k, j[0], j[1]) for k, j in _STATE["jobs"].items() if now - j[2] < KEEP]
                store, busy = dict(_STATE["store"]), set(_STATE["busy"])
            for k, fn, ttl in jobs:
                e = store.get(k)
                if _failed_lately(k, ttl, now):
                    continue
                if k not in busy and (e is None or _stale(e, ttl, now)):
                    _start(k, fn)
                    time.sleep(2)                 # one after another, not all at once
    threading.Thread(target=loop, daemon=True, name="warm-keeper").start()


RETRY = 90                                       # a piece that could not be made is asked for again after this long


def _stale(e, ttl, now=None):
    """Is the piece old? A piece that was slow to make is kept longer (at least six times as long as it took): when the data
    sources crawl (Yahoo slowing the server's address down), the background work calms down by itself instead of piling up."""
    return (now or time.time()) - e["t"] > max(ttl, 6 * float(e.get("took") or 0))


def _failed_lately(key, ttl, now=None):
    t = _STATE["failed"].get(key)
    return t is not None and (now or time.time()) - t < RETRY


def _run(key, fn):
    with _STATE["gate"]:                          # two at a time, in the order they were asked for
        t0 = time.time()
        try:
            val = fn()
            err = None
        except Exception as e:                   # a failed piece keeps the last good one
            val, err = None, f"{type(e).__name__}: {e}"[:200]
    with _STATE["lock"]:
        if val is not None:
            _STATE["store"][key] = {"t": time.time(), "v": val, "took": round(time.time() - t0, 2)}
            _STATE["failed"].pop(key, None)
        else:
            _STATE["failed"][key] = time.time()
            if key in _STATE["store"]:
                _STATE["store"][key]["err"] = err
        _STATE["busy"].pop(key, None)
        ev = _STATE["events"].pop(key, None)
    if ev:
        ev.set()


def _start(key, fn):
    """Start making key in the background unless it is being made already; returns the event set when it is done."""
    with _STATE["lock"]:
        ev = _STATE["events"].get(key)
        if key in _STATE["busy"] and ev:
            return ev
        ev = threading.Event()
        _STATE["events"][key] = ev
        _STATE["busy"][key] = time.time()
    threading.Thread(target=_run, args=(key, fn), daemon=True, name=f"warm-{key}").start()
    return ev


def get(key, fn, ttl, wait=60):
    """The piece key (made by fn, fresh for ttl seconds). Ready: returned at once (made again in the background when old).
    Not ready yet: started (if it isn't already) and waited for, up to wait seconds (None if it isn't done by then; wait=0: never
    waited for - a heavy piece the page can do without until it is ready)."""
    _want(key, fn, ttl)
    with _STATE["lock"]:
        e = _STATE["store"].get(key)
        busy = key in _STATE["busy"]
    if e is not None:
        if _stale(e, ttl) and not busy:
            _start(key, fn)
        return e["v"]
    if _failed_lately(key, ttl):                     # it failed a moment ago: not asked again yet
        return None
    if not wait:
        return None                                  # the keeper makes it in the background (it is wanted now)
    ev = _start(key, fn)
    ev.wait(wait)
    with _STATE["lock"]:
        e = _STATE["store"].get(key)
    return e["v"] if e else None


def prefetch(jobs, want=True):
    """Start every piece of jobs ({key: (fn, ttl)}) that isn't ready or is old, side by side, without waiting. want: a visitor
    wants them (they are kept fresh while visitors come); False: made once ahead of time (another market's pieces)."""
    now = time.time()
    for key, (fn, ttl) in jobs.items():
        if want:
            _want(key, fn, ttl, now)
        with _STATE["lock"]:
            e = _STATE["store"].get(key)
            busy = key in _STATE["busy"]
        if not busy and (e is None or _stale(e, ttl, now)) and not _failed_lately(key, ttl, now):
            _start(key, fn)


def status():
    """{key: (age in seconds, seconds it took to make)} - for the server's report (diag.py)."""
    now = time.time()
    with _STATE["lock"]:
        return {k: (round(now - e["t"]), e.get("took")) for k, e in _STATE["store"].items()}
