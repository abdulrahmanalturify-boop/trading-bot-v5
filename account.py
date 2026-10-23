"""
account.py - Signing in: an account of one's own, with Google, with Apple, or with an email and a password on the site.

Streamlit signs people in itself (st.login, st.user, st.logout) through an identity provider set in the site's Secrets, under
[auth] (with Auth0 as the provider, its one sign-in page offers Google, Apple and an email with a password, and keeps the
passwords, the confirmation emails and the password resets; the site never sees a password). Nothing here works, and nothing
changes on the site, until [auth] is in the Secrets.

A signed-in person gets an account code: a fingerprint of their identity made with the site's secret (cookie_secret), so it can't
be worked out from anything public. Their paper portfolio, Robo Advisor and own bots live under that code, so they open on any
device they sign in on. Without signing in, the site works as before: everything is kept for the browser (p_portfolio).

On the first sign-in on a browser that already has a guest portfolio, Robo Advisor or bots, they move into the account (when the
account has none of its own yet), so nothing made before signing in is lost.

Keep in Secrets (the owner adds them; never in the code, the repository is public):
  [auth]                       redirect_uri = "https://<the site>/oauth2callback", cookie_secret = a long random text
  [auth.auth0]                 client_id, client_secret, server_metadata_url = "https://<tenant>/.well-known/openid-configuration"
  ADMIN_EMAILS (optional)      the owner's sign-in emails, comma-separated: signed in with one of them, the site's own bots and the
                               owner's portfolio open without the password
Changing cookie_secret later changes every account code (accounts would start empty): set it once.
"""
import hashlib
import hmac
import json
import os
import re

import streamlit as st

PREFIX = "acct_"                     # an account code starts with this (a browser's guest code never does)
_CODE = re.compile(r"^acct_[0-9a-f]{40}$")
PREFERRED = ("auth0", "google", "apple", "microsoft")


def _auth():
    try:
        a = st.secrets.get("auth")
    except Exception:
        return None
    return a if a else None


def provider():
    """The provider to sign in with: the name of an [auth.<name>] table (Auth0 first), "" for one unnamed provider set straight in
    [auth], or None when signing in isn't set up."""
    a = _auth()
    if a is None:
        return None
    try:
        names = [k for k in a.keys() if hasattr(a[k], "keys")]
    except Exception:
        names = []
    for p in PREFERRED:
        if p in names:
            return p
    if names:
        return names[0]
    return "" if a.get("client_id") else None


def enabled():
    return provider() is not None and bool((_auth() or {}).get("cookie_secret"))


def _get(u, k):
    try:
        v = u.get(k) if hasattr(u, "get") else getattr(u, k, None)
    except Exception:
        v = None
    return v


def user():
    """{sub, name, email, picture} of the person signed in, or None."""
    if not enabled():
        return None
    try:
        u = st.user
        if not _get(u, "is_logged_in"):
            return None
    except Exception:
        return None
    sub = _get(u, "sub") or _get(u, "email")
    if not sub:
        return None
    email = _get(u, "email")
    name = _get(u, "name") or _get(u, "given_name") or _get(u, "nickname") or (str(email).split("@")[0] if email else "")
    return {"sub": str(sub), "name": str(name or "")[:60], "email": str(email or "")[:120], "picture": _get(u, "picture")}


def code(u=None):
    """The account code of the person signed in (None when nobody is): their identity fingerprinted with the site's secret."""
    u = u or user()
    if not u:
        return None
    secret = str((_auth() or {}).get("cookie_secret") or "")
    if not secret:
        return None
    return PREFIX + hmac.new(secret.encode(), ("tura-account-v1:" + u["sub"]).encode(), hashlib.sha256).hexdigest()[:40]


def is_account(c):
    return isinstance(c, str) and bool(_CODE.match(c))


def is_admin(u=None):
    """Signed in with one of the owner's emails (ADMIN_EMAILS in Secrets), and that email is confirmed by the provider."""
    u = u or user()
    if not u or not u.get("email"):
        return False
    try:
        raw = st.secrets.get("ADMIN_EMAILS") or os.environ.get("ADMIN_EMAILS", "")
    except Exception:
        raw = os.environ.get("ADMIN_EMAILS", "")
    allowed = {e.strip().lower() for e in str(raw).split(",") if e.strip()}
    if not allowed or u["email"].lower() not in allowed:
        return False
    try:
        verified = _get(st.user, "email_verified")
    except Exception:
        verified = None
    return verified is not False                    # a provider that says the email isn't confirmed never makes an admin


def sign_in():
    """Opens the provider's sign-in page (Google, Apple or an email with a password)."""
    p = provider()
    if p is None:
        return
    if p:
        st.login(p)
    else:
        st.login()


def sign_out():
    for k in [k for k in list(st.session_state) if str(k).startswith(("pf_vid", "pb_owner", "acct_"))]:
        del st.session_state[k]
    st.session_state.pop("pb_admin", None)
    st.logout()


# ---------------------------------------------------------------- moving a guest's things into the account
def _move_row(mod, old, new):
    """One stored row (a portfolio or a Robo Advisor) from the guest's key to the account's, when the account has none."""
    import paperbots as PB
    try:
        _, have = mod.load(new)
        _, old_id = mod.load(old)
    except PB.StoreError:
        return False
    if have is not None or old_id is None:
        return False
    if PB.backend() == "supabase":
        url, h = PB._sb()
        r = PB._request("PATCH", url, headers={**h, "Prefer": "return=minimal"}, params={"id": f"eq.{int(old_id)}", "strategy": f"eq.{old}"},
                        data=json.dumps({"strategy": new}))
        PB._check(r)
    else:
        a, b = mod._local_path(old), mod._local_path(new)
        if os.path.exists(a) and not os.path.exists(b):
            os.replace(a, b)
    try:
        mod._load_raw.clear()
    except Exception:
        pass
    return True


def adopt(guest, acct):
    """The first sign-in on a browser with a guest portfolio, Robo Advisor or bots: they move into the account (each kind only
    when the account has none of it yet; bots while the account has room in that market). Returns what moved."""
    import markets as MK
    import paperbots as PB
    import portfolio as PF
    import robo
    moved = []
    if not guest or not acct or guest == acct or is_account(guest):
        return moved
    gk, ak = PF.visitor_key(guest), PF.visitor_key(acct)
    for m in MK.CODES:
        g, a = PF.market_key(gk, m), PF.market_key(ak, m)
        if _move_row(PF, g, a):
            moved.append(("portfolio", m))
        if _move_row(robo, robo.key_for(g), robo.key_for(a)):
            moved.append(("robo", m))
    tg, ta = PB.owner_tag(guest), PB.owner_tag(acct)
    try:
        for b in PB.list_bots(None, tg):
            if len(PB.list_bots(PB.market_of(b), ta)) < PB.MAX_MINE:
                PB.set_owner(b["id"], ta)
                moved.append(("bot", b["id"]))
    except PB.StoreError:
        pass
    return moved


# ---------------------------------------------------------------- the top line: sign in / the account's menu
CSS = """<style>
.st-key-acctsec { position:relative; gap:0 !important; }
.acctbtn { display:flex; align-items:center; gap:4px; height:38px; box-sizing:border-box; padding:0 6px 0 6px; border-radius:11px;
  border:1px solid #3E3A46; background:rgba(255,255,255,.03); color:#fff; font-size:.86rem; font-weight:600; cursor:pointer; white-space:nowrap; }
.acctbtn .av { width:26px; height:26px; border-radius:50%; display:grid; place-items:center; font-weight:800; font-size:.8rem; color:#fff; overflow:hidden;
  background:linear-gradient(140deg,#3B8BEB,#7B45F0); }
.acctbtn .av img { width:100%; height:100%; object-fit:cover; }
.acctbtn .chev { font-size:1rem; color:#9D97A5; transition:transform .2s ease; }
.st-key-acctsec:hover .acctbtn { border-color:rgba(90,160,240,.55); background:linear-gradient(135deg, rgba(59,139,235,.22), rgba(123,69,240,.18)); }
.st-key-acctsec:hover .acctbtn .chev { transform:rotate(180deg); }
.st-key-acctdd { position:absolute !important; top:calc(100% + 8px); right:0; left:auto; width:260px !important; min-width:260px !important; z-index:1000;
  padding:10px; border-radius:16px; background:rgba(20,16,32,.98); border:1px solid rgba(157,151,165,.25); box-shadow:0 22px 50px -20px rgba(0,0,0,.9);
  opacity:0; visibility:hidden; transform:translateY(-6px); transition:opacity .15s ease, transform .15s ease, visibility .15s; pointer-events:none; }
.st-key-acctdd::before { content:""; position:absolute; left:0; right:0; top:-12px; height:12px; }
.st-key-acctsec:hover .st-key-acctdd, .st-key-acctsec:focus-within .st-key-acctdd { opacity:1; visibility:visible; transform:none; pointer-events:auto; }
.accthd { padding:4px 6px 10px; border-bottom:1px solid rgba(255,255,255,.08); margin-bottom:8px; }
.accthd b { display:block; color:#fff; font-size:.95rem; } .accthd small { color:#9D97A5; font-size:.76rem; overflow-wrap:anywhere; }
.accthd .tag { display:inline-block; margin-top:6px; padding:2px 8px; border-radius:99px; font-size:.7rem; color:#C4B5FD; background:rgba(167,139,250,.12); }
.acctbtn.guest { padding:0; width:38px; justify-content:center; }
.acctbtn.guest .ms { font-size:1.35rem; color:#C4B5FD; }
.st-key-acct_in { position:relative; gap:0 !important; }
.st-key-acct_in [data-testid="stElementContainer"] { position:static !important; margin:0 !important; }
.st-key-acct_in .stButton { position:absolute !important; inset:0; z-index:4; margin:0 !important; }
.st-key-acct_in .stButton button { width:100% !important; height:100% !important; min-height:0 !important; opacity:0; cursor:pointer; }
.st-key-acct_in:hover .acctbtn { border-color:rgba(90,160,240,.55); background:linear-gradient(135deg, rgba(59,139,235,.22), rgba(123,69,240,.18)); }
/* the top line is full: room for the account's round button (the search box gives a little) */
[data-testid="stLayoutWrapper"]:has(> .st-key-navsearch), .st-key-topnav > .st-key-navsearch { min-width:150px !important; }
</style>"""


def _initial(u):
    n = (u.get("name") or u.get("email") or "?").strip()
    return n[:1].upper() if n else "?"


def menu(L):
    """The top line's account control: "Sign in" for a guest, the account's menu (who, sign out) for the person signed in.
    Nothing when signing in isn't set up. L: the site's two-language picker."""
    if not enabled():
        return
    import theme as T
    st.markdown(CSS, unsafe_allow_html=True)
    u = user()
    if not u:                                       # a round button like the language one (the top line has little room)
        tip = L("Sign in or create an account: Google, Apple or your email", "سجّل دخول أو أنشئ حساب: Google أو Apple أو إيميلك")
        with st.container(key="acct_in", width="content"):
            st.markdown(f'<div class="acctbtn guest" title="{T.esc(tip)}"><span class="ms">account_circle</span></div>', unsafe_allow_html=True)
            if st.button(L("Sign in", "دخول"), key="acct_login", help=tip):
                sign_in()
        return
    pic = u.get("picture")
    av = f'<img src="{T.esc(pic)}" alt="" referrerpolicy="no-referrer">' if isinstance(pic, str) and pic.startswith("https://") else T.esc(_initial(u))
    first = (u.get("name") or "").split(" ")[0][:16] or L("Account", "حسابي")
    with st.container(key="acctsec", width="content"):
        st.markdown(f'<div class="acctbtn" tabindex="0" title="{T.esc(u.get("name") or first)}"><span class="av">{av}</span>'
                    f'<span class="ms chev">expand_more</span></div>', unsafe_allow_html=True)
        with st.container(key="acctdd"):
            tag = f'<span class="tag">{T.esc(L("Site owner", "صاحب الموقع"))}</span>' if is_admin(u) else ""
            st.markdown(f'<div class="accthd"><b>{T.esc(u.get("name") or first)}</b><small>{T.esc(u.get("email") or "")}</small>{tag}</div>',
                        unsafe_allow_html=True)
            st.caption(L("Your portfolio, Robo Advisor and bots are kept in your account: they open on any device you sign in on.",
                         "محفظتك والمستشار الآلي وبوتاتك محفوظة في حسابك، وتنفتح على أي جهاز تسجّل فيه دخول."))
            if st.button(L("Sign out", "تسجيل الخروج"), icon=":material/logout:", key="acct_logout", width="stretch"):
                sign_out()


def nudge(L, what_en="your bots", what_ar="بوتاتك"):
    """A guest's line where their own things are shown: sign in to keep them on any device."""
    if not enabled() or user():
        return
    import theme as T
    a, b = st.columns([4, 1.2], vertical_alignment="center")
    a.markdown(f'<div style="display:flex;gap:10px;align-items:center;color:#D8D3E2;font-size:.9rem">{T.icon("cloud_sync")}'
               f'<span>{T.esc(L(f"Sign in to keep {what_en} in your account and open them on any device.", f"سجّل دخول عشان تنحفظ {what_ar} في حسابك وتفتحها من أي جهاز."))}</span></div>',
               unsafe_allow_html=True)
    if b.button(L("Sign in", "دخول"), icon=":material/account_circle:", key=f"acct_nudge_{what_en[:6]}", width="stretch"):
        sign_in()


# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "23.4.65"
