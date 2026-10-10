"""
scripts/xbots_run.py - One hourly run of the five X bots (run by .github/workflows/xbots.yml): each bot inside its market's day
reads the new posts of its beat on X (within the shared daily ceiling), updates its reading, trades its paper account while
its market is open and saves everything (Supabase, the paper_bots table).

Needs, in GitHub > Settings > Secrets and variables > Actions:
  X_BEARER_TOKEN  the X API key (a Bearer Token from the X developer console); without it the bots wait
  SUPABASE_URL, SUPABASE_KEY  the site's store (the same as the paper bots); without them nothing is kept
Optional: X_DAILY_READS (posts read a day by the five bots together, 800 by default).
"""
import os
import sys
import warnings

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
warnings.filterwarnings("ignore")

import paperbots as PB      # noqa: E402
import xbots as XB          # noqa: E402


def main():
    if PB.backend() != "supabase":
        print("SUPABASE_URL / SUPABASE_KEY are not set: nothing would be kept, so nothing is read.")
        return 0
    token = os.environ.get("X_BEARER_TOKEN", "").strip()
    force = "--force" in sys.argv
    meta, meta_row = XB.load(XB.META)
    meta = meta or {}
    for bot in XB.BOTS:
        try:
            state = XB.run(bot, token, meta, force=force)
            r = state.get("read") or {}
            led = state["ledger"]
            print(f"{bot['id']:6s} {state['status']:8s} posts {len(state['posts']):3d}  mood6 {r.get('mood6')}  "
                  f"open {len(led['pos'])}  trades {len(led['trades'])}  error {state.get('error')}")
            XB.save_state(bot, state)
        except Exception as e:                       # one bot never stops the others
            print(f"{bot['id']}: {type(e).__name__}: {e}")
    try:
        XB.save(XB.META, meta, meta_row)
    except Exception as e:
        print("meta:", e)
    print(f"posts read today: {meta.get('reads', 0)} of {XB.daily_reads()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
