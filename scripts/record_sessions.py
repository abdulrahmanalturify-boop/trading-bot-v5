"""
scripts/record_sessions.py - Records every Paper Bot's closed sessions right after the US close, even when nobody opens the
site (run by .github/workflows/record.yml). It does exactly what the Paper Bots page does on its first view after a close:
each bot is replayed on the latest prices and the sessions that closed since its last record are saved to Supabase.

Needs SUPABASE_URL and SUPABASE_KEY in the environment (GitHub > Settings > Secrets and variables > Actions).
"""
import os
import sys
import time
import warnings

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
warnings.filterwarnings("ignore")

import paperbots as PB      # noqa: E402  (the site's own bot engine and store)


def main():
    if PB.backend() != "supabase":
        print("SUPABASE_URL / SUPABASE_KEY are not set: nothing to record.")
        return 0
    t0 = time.time()
    bots = PB.list_bots()
    before = {b["id"]: (b.get("fwd") or {}).get("until") for b in bots}
    sims, _ = PB.run_all(bots, hist=False)
    for s in sims:
        b = s["bot"]
        rec = b.get("fwd") or {}
        moved = rec.get("until") != before.get(b["id"])
        print(f"{b['name'][:30]:30s}  recorded until {rec.get('until') or '—'}  {'(new sessions saved)' if moved else '(already up to date)'}"
              f"  {'' if s.get('ok') else 'not run: ' + str(s.get('why'))}")
    print(f"{len(bots)} bots in {time.time() - t0:.0f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
