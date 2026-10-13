"""
warm.py - Data kept ready in the background, so a visitor never waits for it (the home page's news reading, stories, movers,
mood, indicators and heat map). Each piece is computed once for every visitor and kept in this server process; when it gets
old, the next visitor still gets it at once while a fresh one is made in the background. A piece nobody has asked for yet is
started at once and waited for; several pieces asked for together are made side by side.
"""
import sys
import threading
import time

BUILD = "23.4.6"

# kept on sys, so a reload of this module (a new version of the site) keeps what is ready
_STATE = sys.__dict__.setdefault("_tura_warm", {"store": {}, "busy": {}, "lock": threading.Lock(), "events": {}})


def _run(key, fn):
    t0 = time.time()
    try:
        val = fn()
        err = None
    except Exception as e:                       # a failed piece keeps the last good one
        val, err = None, f"{type(e).__name__}: {e}"[:200]
    with _STATE["lock"]:
        if val is not None:
            _STATE["store"][key] = {"t": time.time(), "v": val, "took": round(time.time() - t0, 2)}
        elif key in _STATE["store"]:
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


def get(key, fn, ttl, wait=150):
    """The piece key (made by fn, fresh for ttl seconds). Ready: returned at once (made again in the background when old).
    Not ready yet: started (if it isn't already) and waited for, up to wait seconds (None if it isn't done by then)."""
    with _STATE["lock"]:
        e = _STATE["store"].get(key)
        busy = key in _STATE["busy"]
    if e is not None:
        if time.time() - e["t"] > ttl and not busy:
            _start(key, fn)
        return e["v"]
    ev = _start(key, fn)
    ev.wait(wait)
    with _STATE["lock"]:
        e = _STATE["store"].get(key)
    return e["v"] if e else None


def prefetch(jobs):
    """Start every piece of jobs ({key: (fn, ttl)}) that isn't ready or is old, side by side, without waiting."""
    now = time.time()
    for key, (fn, ttl) in jobs.items():
        with _STATE["lock"]:
            e = _STATE["store"].get(key)
            busy = key in _STATE["busy"]
        if not busy and (e is None or now - e["t"] > ttl):
            _start(key, fn)


def status():
    """{key: (age in seconds, seconds it took to make)} - for the server's report (diag.py)."""
    now = time.time()
    with _STATE["lock"]:
        return {k: (round(now - e["t"]), e.get("took")) for k, e in _STATE["store"].items()}
