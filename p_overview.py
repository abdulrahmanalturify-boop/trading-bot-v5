"""
p_overview.py - The home page (Overview), the site's first screen since 23.4: the logo and the main prices, then what is
moving the market today, starting with what's trending (the breaking stories, the top three stories, the companies in the
news, the market summary and the movers), the market's mood (fear and greed, the news mood), the heat map and the markets.
The site's tools are cards placed between the parts, like adverts in a magazine (one on the right, two on the left, ...).
Replaces the landing ("Beyond investment") and the old overview.
"""
import os
import time

import streamlit as st

import pandas as pd

import data
import home
import markets as MK
import p_calendar as PC
import p_insight as PI
import p_markets as PM
import p_newsintel as PNI
import theme as T
import ui
import tasi
import universe as U
import warm
from i18n import L, is_ar
from sp500 import SP500

ss = st.session_state
_PROF = os.environ.get("TURA_PROFILE") == "1"       # the site check's speed run: how long each part of the page takes


def _timed(label, fn, *a):
    t0 = time.time()
    try:
        return fn(*a)
    finally:
        if _PROF:
            print(f"[prof] {label} {time.time() - t0:.2f}s", flush=True)

# ---------------------------------------------------------------- the tools, as adverts placed between the page's sections
# (key, page, icon, tone, kicker, title, pitch, call to action). "ai" opens the chat window instead of a page.
TOOLS = {
    "ai": (None, "auto_awesome", "ai", ("AI assistant", "مساعد ذكي"), ("TURA AI", "TURA AI"),
           ("Stuck on a number, a chart or a word? Ask, and get it explained in plain words.",
            "وقفت عند رقم أو رسم أو مصطلح؟ اسأل، ويشرح لك بكلام بسيط."), ("Ask the AI assistant", "اسأل المساعد الذكي")),
    "hunt": ("scanner", "radar", "hunt", ("Daily picks", "فرص يومية"), ("Opportunity Hunter", "صائد الفرص"),
             ("Today's setups, scored out of 100, each with a full trade plan.",
              "فرص اليوم بدرجة من 100، ولكل فرصة خطة تداول كاملة."), ("See today's picks", "شوف فرص اليوم")),
    "bots": ("paper", "smart_toy", "bots", ("Automation", "أتمتة"), ("Paper Bots", "البوتات الافتراضية"),
             ("Build a trading bot in a minute and watch it trade virtual money for you.",
              "ابنِ بوت تداول بدقيقة، وشوفه يتداول عنك بفلوس افتراضية."), ("Build my bot", "ابنِ بوتي")),
    "pf": ("pf_dash", "account_balance_wallet", "pf", ("Practice", "تدرّب"), ("Paper trading", "التداول الافتراضي"),
           ("Trade at real prices with virtual money: learn without risking a cent of your own.",
            "تداول بأسعار حقيقية وفلوس افتراضية: تعلّم بدون ما تخاطر بفلوسك."), ("Open my portfolio", "افتح محفظتي")),
    "robo": ("pf_robo", "psychology", "robo", ("Planning", "تخطيط"), ("Robo Advisor", "المستشار الآلي"),
             ("Answer a few questions and get a portfolio built around your goal and your risk.",
              "جاوب على كم سؤال، وخذ محفظة مبنية على هدفك ومخاطرتك."), ("Get my plan", "خذ خطتي")),
    "academy": ("academy", "school", "academy", ("Learning", "تعلّم"), ("Academy", "الأكاديمية"),
                ("From your first share to options: short courses with labs on real charts.",
                 "من أول سهم إلى الخيارات: دورات قصيرة مع تطبيقات على رسوم حقيقية."), ("Start learning", "ابدأ التعلّم")),
    "xbots": ("xbots", "alternate_email", "x", ("Social signals", "إشارات X"), ("X Bots", "بوتات X"),
              ("Bots that read X every hour and trade on the crowd's mood. Which one reads it right?",
               "بوتات تقرأ X كل ساعة وتتداول على مزاج الناس. مين فيها يقراه صح؟"), ("Meet the bots", "تعرّف عليها")),
    "screener": ("screener", "filter_alt", "scr", ("Research", "بحث"), ("Screener", "فلتر الأسهم"),
                 ("Find the stocks that fit you, from hundreds, in a few clicks.",
                  "لقّ الأسهم اللي تناسبك من بين المئات، بكم ضغطة."), ("Open the screener", "افتح الفلتر")),
}


CSS = """<style data-lm="keep">
/* ---- a part of the page with its tool cards beside it: the cards stay in view while that part is read */
[data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"] > div[class*="st-key-ovads_"]),
[data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] div[class*="st-key-ovads_"]){align-items:flex-start!important}
[data-testid="stColumn"]:has(div[class*="st-key-ovads_"]){position:sticky;top:80px;align-self:flex-start;z-index:2}
div[class*="st-key-ovads_"]{gap:16px!important;padding-top:18px}
div[class*="st-key-ovbody_"] .msg{grid-template-columns:repeat(2,minmax(0,1fr))!important}
/* ---- the card: a coloured poster with its tool's picture, name, promise, three points and a call to action; the whole card
   opens the tool. Hovered, it lifts, light sweeps across it and the arrow moves on. */
@keyframes ovshine{from{transform:translateX(-120%) skewX(-18deg)}to{transform:translateX(320%) skewX(-18deg)}}
@keyframes ovin{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@keyframes ovdot{0%,80%,100%{opacity:.25;transform:translateY(0)}40%{opacity:1;transform:translateY(-3px)}}
@keyframes ovspin{to{transform:rotate(360deg)}}
@keyframes ovping{0%,100%{r:3.6px;opacity:1}50%{r:6px;opacity:.55}}
@keyframes ovdraw{from{stroke-dashoffset:520}to{stroke-dashoffset:0}}
@keyframes ovlive{0%{box-shadow:0 0 0 0 rgba(74,222,128,.7)}70%{box-shadow:0 0 0 6px rgba(74,222,128,0)}100%{box-shadow:0 0 0 0 rgba(74,222,128,0)}}
div[class*="st-key-ovad_"]{position:relative}
div[class*="st-key-ovad_"] [data-testid="stElementContainer"]:has([data-testid="stButton"]){position:absolute!important;inset:0;z-index:3;margin:0!important}
div[class*="st-key-ovad_"] [data-testid="stButton"],div[class*="st-key-ovad_"] [data-testid="stButton"] button{width:100%!important;height:100%!important;min-height:100%!important}
div[class*="st-key-ovad_"] [data-testid="stButton"] button{opacity:0!important;cursor:pointer}
.ovad{position:relative;overflow:hidden;isolation:isolate;border-radius:22px;padding:16px 16px 18px;color:#fff;background:radial-gradient(120% 90% at 100% 0%,rgba(255,255,255,.16),transparent 55%),linear-gradient(155deg,var(--a1),var(--a2));
  border:1px solid rgba(255,255,255,.14);box-shadow:0 1px 0 rgba(255,255,255,.18) inset,0 20px 40px -24px var(--sh);transition:transform .32s cubic-bezier(.2,.8,.2,1),box-shadow .32s ease;cursor:pointer;animation:ovin .5s ease-out both}
.ovad::after{content:"";position:absolute;top:-10%;bottom:-10%;width:34%;left:0;z-index:2;pointer-events:none;background:linear-gradient(90deg,transparent,rgba(255,255,255,.22),transparent);transform:translateX(-120%) skewX(-18deg)}
div[class*="st-key-ovad_"]:hover .ovad,.ovad.solo:hover{transform:translateY(-4px);box-shadow:0 1px 0 rgba(255,255,255,.2) inset,0 28px 48px -22px var(--sh)}
div[class*="st-key-ovad_"]:hover .ovad::after,.ovad.solo:hover::after{animation:ovshine .9s ease}
.ovad .big{position:absolute;inset-inline-end:-18px;bottom:-30px;z-index:-1;font-family:"Material Symbols Rounded";font-size:130px;line-height:1;color:#fff;opacity:.09;transform:rotate(-12deg);transition:transform .6s cubic-bezier(.2,.8,.2,1)}
div[class*="st-key-ovad_"]:hover .ovad .big,.ovad.solo:hover .big{transform:rotate(-2deg) scale(1.08)}
.ovad .k{display:flex;align-items:center;justify-content:space-between;gap:8px;font-size:10.5px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.8)}
.ovad.rtl .k{letter-spacing:0;font-size:11.5px}
.ovad .k>span{display:inline-flex;align-items:center;gap:8px}
.ovad .k .ic{width:28px;height:28px;border-radius:9px;display:grid;place-items:center;background:rgba(255,255,255,.18);box-shadow:inset 0 1px 0 rgba(255,255,255,.22)}
.ovad .k .ic .ms{font-size:17px;color:#fff}
.ovad .k em{font-style:normal;letter-spacing:.04em;padding:3px 9px;border-radius:999px;background:rgba(255,255,255,.95);color:var(--a2);font-weight:800}
.ovad .vz{position:relative;margin:14px 0 14px;height:118px;border-radius:16px;background:rgba(5,8,25,.26);border:1px solid rgba(255,255,255,.12);box-shadow:inset 0 1px 0 rgba(255,255,255,.08);overflow:hidden}
.ovad .tt{display:block;font-size:19px;font-weight:800;line-height:1.25;color:#fff;letter-spacing:-.01em}
.ovad p{margin:6px 0 10px;font-size:13px;line-height:1.6;color:rgba(255,255,255,.88)}
.ovad ul{list-style:none;margin:0 0 14px;padding:0;display:flex;flex-direction:column;gap:6px}
.ovad li{display:flex;align-items:flex-start;gap:7px;font-size:12.5px;line-height:1.45;color:rgba(255,255,255,.92)}
.ovad li .ms{font-size:16px;color:#fff;opacity:.9;margin-top:1px}
.ovad .go{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;box-sizing:border-box;padding:10px 14px;border-radius:13px;font-size:13.5px;font-weight:800;color:var(--a2);background:#fff;box-shadow:0 8px 18px -10px rgba(0,0,0,.45);transition:transform .25s ease}
.ovad .go .ms{font-size:18px;transition:transform .25s cubic-bezier(.2,.8,.2,1)}
.ovad.rtl .go .ms{transform:scaleX(-1)}
div[class*="st-key-ovad_"]:hover .ovad .go .ms,.ovad.solo:hover .go .ms{transform:translateX(4px)}
div[class*="st-key-ovad_"]:hover .ovad.rtl .go .ms,.ovad.solo.rtl:hover .go .ms{transform:scaleX(-1) translateX(4px)}
/* the colours of each tool */
.ovad.ai{--a1:#1E3A8A;--a2:#6D28D9;--sh:rgba(79,70,229,.8)}
.ovad.hunt{--a1:#0E7490;--a2:#1D4ED8;--sh:rgba(14,116,144,.75)}
.ovad.bots{--a1:#7C3AED;--a2:#BE185D;--sh:rgba(147,51,234,.75)}
.ovad.pf{--a1:#047857;--a2:#0E7490;--sh:rgba(4,120,87,.75)}
.ovad.robo{--a1:#0F766E;--a2:#4338CA;--sh:rgba(15,118,110,.75)}
.ovad.academy{--a1:#C2410C;--a2:#9D174D;--sh:rgba(194,65,12,.7)}
.ovad.x{--a1:#0F172A;--a2:#334155;--sh:rgba(15,23,42,.8)}
.ovad.scr{--a1:#1E40AF;--a2:#0369A1;--sh:rgba(30,64,175,.75)}
/* the pictures */
.vz.chat{display:flex;flex-direction:column;gap:7px;padding:10px 11px;height:auto!important;min-height:118px;box-sizing:border-box}
.vz.chat .q{align-self:flex-end;max-width:82%;padding:6px 10px;border-radius:12px;border-end-end-radius:4px;background:rgba(255,255,255,.92);color:#312E81;font-size:12px;font-weight:700;animation:ovin .5s .1s ease-out both}
.ovad.rtl .vz.chat .q{align-self:flex-start}
.vz.chat .a{display:flex;gap:7px;align-items:flex-start;font-size:11.5px;line-height:1.5;color:rgba(255,255,255,.92);animation:ovin .5s .6s ease-out both}
.vz.chat .a i{flex:none;width:20px;height:20px;border-radius:50%;display:grid;place-items:center;font-style:normal;font-size:10px;background:linear-gradient(135deg,#60A5FA,#A78BFA)}
.vz.chat .ty{display:flex;gap:4px;padding-inline-start:27px}
.vz.chat .ty b{width:5px;height:5px;border-radius:50%;background:#C4B5FD;animation:ovdot 1.2s infinite ease-in-out}
.vz.chat .ty b:nth-child(2){animation-delay:.15s}.vz.chat .ty b:nth-child(3){animation-delay:.3s}
.vz.radar svg,.vz.bot svg,.vz.funnel svg{display:block;width:100%;height:100%}
.vz.radar text{font-size:9.5px;font-weight:700;fill:rgba(255,255,255,.85);font-family:inherit}
.vz.radar .sw{transform-origin:59px 59px;animation:ovspin 3.6s linear infinite}
.vz.radar .pd{animation:ovping 2.4s ease-in-out infinite}
.vz.bot .lv{position:absolute;top:9px;inset-inline-start:10px;z-index:2;display:inline-flex;align-items:center;gap:6px;padding:3px 8px;border-radius:999px;background:rgba(0,0,0,.35);font-size:10px;font-weight:800;letter-spacing:.08em}
.vz.bot .lv i{width:6px;height:6px;border-radius:50%;background:#4ADE80;animation:ovlive 1.8s infinite}
.vz.bot .ft{position:absolute;top:11px;inset-inline-end:10px;z-index:2;font-size:10.5px;color:rgba(255,255,255,.75)}
.vz.bot svg{position:absolute;inset:auto 0 0 0;height:82px}
.vz.bot .ln{stroke-dasharray:520;animation:ovdraw 2.2s ease-out both}
.vz.ticket{display:flex;flex-direction:column;justify-content:center;gap:6px;padding:12px 14px;box-sizing:border-box}
.vz.ticket .l{font-size:11px;color:rgba(255,255,255,.75)}
.vz.ticket .v{font-size:26px;font-weight:800;letter-spacing:-.01em;direction:ltr;text-align:start}
.ovad.rtl .vz.ticket .v{text-align:right}
.vz.ticket .bs{display:flex;gap:8px}
.vz.ticket .bs span{flex:1;text-align:center;padding:6px 0;border-radius:10px;font-size:12px;font-weight:800}
.vz.ticket .b{background:#22C55E;color:#052E16}.vz.ticket .s{background:rgba(255,255,255,.16);color:#fff;border:1px solid rgba(255,255,255,.25)}
.vz.donut{display:flex;align-items:center;gap:12px;padding:10px 12px;box-sizing:border-box}
.vz.donut svg{flex:none;width:96px;height:96px}
.vz.donut svg circle{animation:ovin .6s ease-out both}
.vz.donut .lg{display:grid;grid-template-columns:1fr 1fr;gap:6px 10px;font-size:11.5px}
.vz.donut .lg span{display:flex;align-items:center;gap:6px}
.vz.donut .lg i{width:9px;height:9px;border-radius:3px}
.vz.crs{display:flex;flex-direction:column;justify-content:center;gap:9px;padding:10px 12px;box-sizing:border-box}
.vz.crs .r{display:flex;align-items:center;gap:9px}
.vz.crs .n{flex:none;width:22px;height:22px;border-radius:7px;display:grid;place-items:center;font-size:11px;font-weight:800;background:rgba(255,255,255,.18)}
.vz.crs .t{flex:1;min-width:0}
.vz.crs b{display:block;font-size:11.5px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.vz.crs .bar{height:5px;margin-top:4px;border-radius:9px;background:rgba(255,255,255,.18);overflow:hidden}
.vz.crs .bar i{display:block;height:100%;border-radius:9px;background:linear-gradient(90deg,#FDE68A,#FCA5A5)}
.vz.feed{display:flex;flex-direction:column;justify-content:center;gap:8px;padding:10px 12px;box-sizing:border-box}
.vz.feed .p{display:flex;align-items:center;gap:8px}
.vz.feed .av{flex:none;width:24px;height:24px;border-radius:50%;display:grid;place-items:center;font-size:12px;font-weight:800;background:rgba(255,255,255,.16)}
.vz.feed .ln{flex:1;display:flex;flex-direction:column;gap:4px}
.vz.feed .ln i{display:block;height:5px;border-radius:9px;background:rgba(255,255,255,.22)}
.vz.feed .up,.vz.feed .dn{flex:none;font-size:10.5px;font-weight:800;padding:2px 7px;border-radius:999px}
.vz.feed .up{background:rgba(74,222,128,.2);color:#86EFAC}.vz.feed .dn{background:rgba(248,113,113,.2);color:#FCA5A5}
.vz.funnel{display:flex;flex-direction:column;gap:4px;padding:10px 10px 8px;box-sizing:border-box}
.vz.funnel .ch{display:flex;flex-wrap:wrap;gap:5px;justify-content:center}
.vz.funnel .ch span{font-size:10.5px;font-weight:700;padding:3px 8px;border-radius:999px;background:rgba(255,255,255,.18)}
.vz.funnel svg{height:40px}
.vz.funnel .rs{display:flex;justify-content:center;gap:6px}
.vz.funnel .rs i{width:36px;height:6px;border-radius:9px;background:rgba(255,255,255,.35)}
/* the wide cards at the foot of the page: the picture beside the words */
.ovad.wide .bd{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.15fr);gap:18px;align-items:center}
.ovad.wide .vz{margin:12px 0 0;height:100%;min-height:150px}
/* the earnings card under an advert */
.ovearnh{display:flex;align-items:center;gap:8px;margin:2px 4px 8px;font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#8E97AD}
.ovearnh .ms{font-size:17px}
.ehub.one{grid-template-columns:1fr!important;margin:0!important}
.ehub.one .day{border-radius:18px}
div.st-key-ovearn [data-testid="stButton"] button{min-height:34px!important;border-radius:999px!important;font-size:12.5px!important}
/* the mood row: the two dials side by side, the same height */
div.st-key-ovmood [data-testid="stHorizontalBlock"]{align-items:stretch!important}
div.st-key-ovmood [data-testid="stColumn"]>div{height:100%}
.ovcard{height:100%;box-sizing:border-box;padding:14px 14px 10px;border-radius:18px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08)}
.ovcard .h{display:flex;align-items:center;gap:8px;font-size:13px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#C9C4D3;margin-bottom:6px}
.ovcard .h .ms{font-size:18px}
div.st-key-ovmood .nie-hc{height:100%;box-sizing:border-box}
div.st-key-ovmore [data-testid="stButton"] button{border-radius:999px!important}
div.st-key-ovfoot{margin-top:8px}
div.st-key-ovads_z{flex-direction:row!important;gap:22px!important;padding-top:0}
div.st-key-ovads_z>*{flex:1 1 0!important;min-width:0!important}
/* a narrow page (a phone, a tablet, a computer with the side panel open on a small screen - measured on the page itself, not
   the screen): the part first, then its cards side by side (sliding across when there are two) */
div.st-key-ovpage{container-type:inline-size;container-name:ovp}
@container ovp (max-width:820px){
  [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] div[class*="st-key-ovads_"]){flex-direction:column!important;flex-wrap:nowrap!important;gap:10px!important}
  [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] div[class*="st-key-ovads_"])>[data-testid="stColumn"]{width:100%!important;flex:1 1 auto!important;min-width:0!important;max-width:100%!important}
  [data-testid="stColumn"]:has(div[class*="st-key-ovads_"]){position:static;order:2}
  div[class*="st-key-ovads_"]{flex-direction:row!important;overflow-x:auto;overflow-y:hidden;scroll-snap-type:x mandatory;padding:4px 2px 12px;scrollbar-width:none}
  div[class*="st-key-ovads_"]::-webkit-scrollbar{display:none}
  div[class*="st-key-ovads_"]>*{flex:1 0 300px!important;min-width:300px!important;max-width:420px;scroll-snap-align:start}
  .ovad.wide .bd{grid-template-columns:1fr}
  div[class*="st-key-ovbody_"] .msg{grid-template-columns:minmax(0,1fr)!important}
}
@container ovp (max-width:520px){div[class*="st-key-ovads_"]>*{flex-basis:84%!important;min-width:84%!important}}
@media (prefers-reduced-motion:reduce){.ovad,.ovad *,.ovad::after{animation:none!important;transition:none!important}}
</style>"""


def _facts():
    f = home._facts()
    try:
        import paperbots as PB
        f["mine"] = PB.MAX_MINE
    except Exception:
        f["mine"] = 3
    try:
        import robo
        f["questions"] = len(robo.QUESTIONS)
    except Exception:
        f["questions"] = 0
    try:
        import tasi
        f["sa_stocks"] = len(tasi.SYMBOLS)
    except Exception:
        f["sa_stocks"] = 0
    f["top"] = len(U.US_UNIVERSE)
    try:
        import portfolio as PF
        f["cash"] = PF.DEFAULTS["start_cash"]
    except Exception:
        f["cash"] = 100000.0
    try:
        import academy as A
        f["course_titles"] = [L(*c["title"]) for c in A.COURSES[:3]]
    except Exception:
        f["course_titles"] = []
    return f


def _points(key, f, sa):
    """Three things the tool gives, with the site's own numbers."""
    n = f"{f['sa_stocks']}" if sa else f"{f['top']}"
    cash = MK.money(f["cash"])
    return {
        "ai": [L("Explains the numbers on the page you're on", "يشرح أرقام الصفحة اللي أنت فيها"),
               L("Answers in Arabic or English", "يجاوب بالعربي أو الإنجليزي"), L("Free, no sign-up needed", "مجاني، بدون تسجيل")],
        "hunt": [L(f"Scans {n} stocks for you", f"يفحص لك {n} سهم"), L("A score out of 100 for every setup", "درجة من 100 لكل فرصة"),
                 L("Entry, stop and target for each pick", "دخول ووقف وهدف لكل فرصة")],
        "bots": [L(f"{f['single']} strategies and {f['combined']} combinations", f"{f['single']} استراتيجية و{f['combined']} تركيبة"),
                 L("Ready-made bots, or build your own", "بوتات جاهزة، أو ابنِ بوتك"),
                 L(f"Up to {f['mine']} bots of your own, free", f"لين {f['mine']} بوتات خاصة فيك، مجاناً")],
        "pf": [L(f"{cash} of virtual money to start", f"{cash} فلوس افتراضية تبدأ فيها"), L("Real market prices", "أسعار السوق الحقيقية"),
               L("A health score for your portfolio", "تقييم لصحة محفظتك من 100")],
        "robo": [L(f"{f['questions']} short questions", f"{f['questions']} سؤال قصير"), L("A portfolio built for your goal", "محفظة مبنية على هدفك"),
                 L("Follow it with virtual money", "تابعها بفلوس افتراضية")],
        "academy": [L(f"{f['courses']} courses, beginner to advanced", f"{f['courses']} دورات من المبتدئ للمتقدم"),
                    L(f"{f['labs']} hands-on labs", f"{f['labs']} تطبيق عملي"), L(f"{f['terms']} terms explained", f"{f['terms']} مصطلح مشروح")],
        "xbots": [L("Five bots, each on its own beat", "خمس بوتات، كل واحد له تخصص"), L("They read X every hour of the trading day", "تقرأ X كل ساعة وقت التداول"),
                  L("A log shows which one is right", "سجل يبين مين فيها يصيب")],
        "screener": [L("Descriptive, fundamental and technical filters", "فلاتر وصفية وأساسية وفنية"),
                     L("Ready presets and investment themes", "قوالب جاهزة وثيمات استثمارية"), L("Open any company in one click", "افتح أي شركة بضغطة")],
    }[key]


# ---------------------------------------------------------------- each card's picture (drawn, no made-up numbers)
def _vz(key, f):
    ar = is_ar()
    if key == "ai":
        q = L("What does RSI mean?", "وش يعني مؤشر RSI؟")
        a = L("A momentum gauge from 0 to 100: above 70 the stock may be overbought, under 30 oversold.",
              "مقياس زخم من 0 إلى 100: فوق 70 ممكن يكون السهم متشبّع شراء، وتحت 30 متشبّع بيع.")
        return (f'<div class="vz chat"><div class="q">{T.esc(q)}</div><div class="a"><i>✦</i><span>{T.esc(a)}</span></div>'
                '<div class="ty"><b></b><b></b><b></b></div></div>')
    if key == "hunt":
        lt, le, ls = L("Target", "الهدف"), L("Entry", "الدخول"), L("Stop", "الوقف")
        dots = [(52, 30), (78, 48), (40, 72), (70, 86), (30, 44)]
        return ('<div class="vz radar"><svg viewBox="0 0 220 118" aria-hidden="true"><defs><linearGradient id="ovswp" x1="0" y1="0" x2="1" y2="1">'
                '<stop offset="0" stop-color="#7DD3FC" stop-opacity=".55"/><stop offset="1" stop-color="#7DD3FC" stop-opacity="0"/></linearGradient></defs>'
                + "".join(f'<circle cx="59" cy="59" r="{r}" fill="none" stroke="rgba(255,255,255,.18)"/>' for r in (18, 36, 53))
                + '<g class="sw"><path d="M59 59 L59 6 A53 53 0 0 1 105 33 Z" fill="url(#ovswp)"/></g>'
                + "".join(f'<circle class="pd" style="animation-delay:{i * .45:.2f}s" cx="{x}" cy="{y}" r="3.6" fill="#86EFAC"/>' for i, (x, y) in enumerate(dots))
                + '<circle cx="59" cy="59" r="3" fill="#7DD3FC"/>'
                '<path d="M132 92 L146 80 L158 86 L172 62 L186 66 L204 34" fill="none" stroke="rgba(255,255,255,.75)" stroke-width="2" stroke-linejoin="round"/>'
                f'<line x1="128" y1="30" x2="214" y2="30" stroke="#4ADE80" stroke-dasharray="4 3"/><text x="214" y="25" text-anchor="end">{T.esc(lt)}</text>'
                f'<line x1="128" y1="62" x2="214" y2="62" stroke="#93C5FD"/><text x="214" y="57" text-anchor="end">{T.esc(le)}</text>'
                f'<line x1="128" y1="100" x2="214" y2="100" stroke="#F87171" stroke-dasharray="4 3"/><text x="214" y="114" text-anchor="end">{T.esc(ls)}</text>'
                '</svg></div>')
    if key == "bots":
        pts = [(0, 92), (24, 86), (48, 90), (72, 72), (96, 78), (120, 60), (144, 66), (168, 48), (192, 54), (216, 34), (240, 38), (264, 20)]
        line = "M" + " L".join(f"{x} {y}" for x, y in pts)
        buys, sells = [(72, 72), (168, 48)], [(144, 66)]
        return ('<div class="vz bot"><div class="lv"><i></i>LIVE</div><span class="ft">' + T.esc(L("Forward test", "اختبار أمامي")) + '</span>'
                '<svg viewBox="0 0 264 110" preserveAspectRatio="none" aria-hidden="true"><defs><linearGradient id="ovba" x1="0" y1="0" x2="0" y2="1">'
                '<stop offset="0" stop-color="#F0ABFC" stop-opacity=".45"/><stop offset="1" stop-color="#F0ABFC" stop-opacity="0"/></linearGradient></defs>'
                f'<path d="{line} L264 110 L0 110 Z" fill="url(#ovba)"/><path class="ln" d="{line}" fill="none" stroke="#fff" stroke-width="2.4" stroke-linejoin="round"/>'
                + "".join(f'<path d="M{x - 6} {y + 14} L{x} {y + 5} L{x + 6} {y + 14} Z" fill="#4ADE80"/>' for x, y in buys)
                + "".join(f'<path d="M{x - 6} {y - 14} L{x} {y - 5} L{x + 6} {y - 14} Z" fill="#FCA5A5"/>' for x, y in sells)
                + '</svg></div>')
    if key == "pf":
        return (f'<div class="vz ticket"><div class="l">{T.esc(L("Virtual cash", "رصيدك الافتراضي"))}</div><div class="v">{T.esc(MK.money(f["cash"]))}</div>'
                f'<div class="bs"><span class="b">{T.esc(L("Buy", "شراء"))}</span><span class="s">{T.esc(L("Sell", "بيع"))}</span></div></div>')
    if key == "robo":
        segs = [("#A5B4FC", 46), ("#5EEAD4", 28), ("#FDE68A", 16), ("#F9A8D4", 10)]
        circ, off, arcs = 2 * 3.14159 * 34, 0.0, ""
        for col, pc in segs:
            ln = circ * pc / 100
            arcs += (f'<circle cx="50" cy="50" r="34" fill="none" stroke="{col}" stroke-width="13" stroke-dasharray="{ln - 2:.1f} {circ - ln + 2:.1f}" '
                     f'stroke-dashoffset="{-off:.1f}" transform="rotate(-90 50 50)"/>')
            off += ln
        names = [L("Stocks", "أسهم"), L("Bonds", "سندات"), L("Gold", "ذهب"), L("Cash", "كاش")]
        leg = "".join(f'<span><i style="background:{c}"></i>{T.esc(n)}</span>' for (c, _), n in zip(segs, names))
        return f'<div class="vz donut"><svg viewBox="0 0 100 100" aria-hidden="true">{arcs}</svg><div class="lg">{leg}</div></div>'
    if key == "academy":
        rows = f["course_titles"] or [L("How the Stock Market Works", "كيف يعمل سوق الأسهم")]
        return ('<div class="vz crs">' + "".join(
            f'<div class="r"><span class="n">{i + 1}</span><div class="t"><b>{T.esc(t)}</b><div class="bar"><i style="width:{w}%"></i></div></div></div>'
            for i, (t, w) in enumerate(zip(rows, (100, 55, 15)))) + "</div>")
    if key == "xbots":
        return ('<div class="vz feed">'
                f'<div class="p"><span class="av">@</span><div class="ln"><i style="width:82%"></i><i style="width:56%"></i></div><span class="up">▲ {T.esc(L("bullish", "صاعد"))}</span></div>'
                f'<div class="p"><span class="av">@</span><div class="ln"><i style="width:70%"></i><i style="width:44%"></i></div><span class="dn">▼ {T.esc(L("bearish", "هابط"))}</span></div>'
                f'<div class="p"><span class="av">@</span><div class="ln"><i style="width:88%"></i><i style="width:60%"></i></div><span class="up">▲ {T.esc(L("bullish", "صاعد"))}</span></div></div>')
    if key == "screener":
        chips = [L("Descriptive", "وصفية"), L("Fundamental", "أساسية"), L("Technical", "فنية"), L("Themes", "ثيمات"), L("Presets", "قوالب")]
        return ('<div class="vz funnel"><div class="ch">' + "".join(f'<span>{T.esc(c)}</span>' for c in chips) + '</div>'
                '<svg viewBox="0 0 220 46" aria-hidden="true"><path d="M20 4 H200 L136 30 V44 H84 V30 Z" fill="rgba(255,255,255,.16)" stroke="rgba(255,255,255,.45)"/></svg>'
                '<div class="rs"><i></i><i></i><i></i></div></div>')
    return ""


def _ad_html(key, f, sa, wide=False):
    page, icon, tone, kick, title, pitch, cta = TOOLS[key]
    ar = is_ar()
    solo = key == "ai"
    attrs = ' data-open-ai="1" role="button" tabindex="0"' if solo else ""
    pts = "".join(f'<li>{T.icon("check_circle")}<span>{T.esc(x)}</span></li>' for x in _points(key, f, sa))
    text = (f'<div class="tx"><b class="tt">{T.esc(L(*title))}</b><p>{T.esc(L(*pitch))}</p><ul>{pts}</ul>'
            f'<span class="go">{T.esc(L(*cta))}{T.icon("arrow_forward")}</span></div>')
    return (f'<div class="ovad {tone}{" rtl" if ar else ""}{" solo" if solo else ""}{" wide" if wide else ""}" data-nogq{attrs}>'
            f'<span class="big" aria-hidden="true">{icon}</span>'
            f'<div class="k"><span><span class="ic">{T.icon(icon)}</span>{T.esc(L(*kick))}</span><em>{T.esc(L("Free", "مجاني"))}</em></div>'
            f'<div class="bd">{_vz(key, f)}{text}</div></div>')


def _open_tool(key, page):
    if key == "bots":                               # the visitor's own bots, the new bot's form open (p_paper)
        ss["pb_view"] = "mine"
        ss["pb_build"] = True
    ss["goto"] = page


def _available(key, sa):
    page = TOOLS[key][0] if key in TOOLS else None
    if key == "earn":
        return not sa
    return key in TOOLS and (page is None or not sa or page in MK.SA_PAGES)


def _card(key, f, sa, wide=False):
    if key == "earn":                               # the next session's earnings (a card of the earnings calendar)
        with st.container(key="ovearn"):
            got = _timed("earnings", ui.safe, PC.next_session_html, 8)
            if got:
                ui.html(f'<div class="ovearnh">{T.icon("event_upcoming")}{T.esc(L("Earnings next session", "أرباح الجلسة الجاية"))}</div>' + got)
                st.button(L("Earnings calendar", "مواعيد الأرباح"), key="ovgo_earn", icon=":material/event_upcoming:", width="stretch",
                          on_click=_open_tool, args=("earn", "earnings"))
        return
    if key == "ai":                                 # the chat window opens on the page (theme.FX_JS presses the AI button)
        ui.html(_ad_html(key, f, sa, wide))
        return
    with st.container(key=f"ovad_{key}"):
        ui.html(_ad_html(key, f, sa, wide))
        st.button(L(*TOOLS[key][4]), key=f"ovgo_{key}", on_click=_open_tool, args=(key, TOOLS[key][0]), width="stretch")


def _with_ads(tag, side, keys, f, sa, body):
    """A part of the page with tool cards beside it, on the given side of the screen ("right" or "left", whatever the page's
    language); the cards stay in view while that part is read. On a phone they come after it."""
    keys = [k for k in keys if _available(k, sa)]
    if not keys:
        body()
        return None
    ad_first = (side == "right") == is_ar()         # an Arabic page lays its columns out from the right
    cols = st.columns([1, 2.65] if ad_first else [2.65, 1], gap="large")
    ad_col, main_col = (cols[0], cols[1]) if ad_first else (cols[1], cols[0])
    with ad_col:                                    # the cards first: they show at once while the part's data comes in
        with st.container(key=f"ovads_{tag}"):
            for k in keys:
                _card(k, f, sa)
    with main_col:
        with st.container(key=f"ovbody_{tag}"):
            return body()


def _chips(px, sa):
    chips = ""
    if sa:
        for s_ in ("^TASI.SR", "2222.SR", "1120.SR", "BZ=F", "GC=F", "DX-Y.NYB"):
            p, _, c = PM._last(px, s_)
            if p is not None:
                chips += f'<span class="chip"><b>{T.esc(PM._sa_name(s_))}</b>{T.fmt_price(p)} {T.pill(c)}</span>'
        return chips
    for s_, name in (("^GSPC", "S&P 500"), ("^IXIC", "NASDAQ"), ("^DJI", "DOW"), ("^TNX", "US10Y"), ("GC=F", "GOLD"), ("BTC-USD", "BTC")):
        p, _, c = PM._last(px, s_)
        if p is not None:
            chips += f'<span class="chip"><b>{name}</b>{f"{p:.2f}%" if s_ == "^TNX" else T.fmt_price(p)} {T.pill(c)}</span>'
            ui.ai_note(name, f"{p:,.2f} ({c:+.2f}% today)" if c is not None else f"{p:,.2f}")
    return chips


def _pick_news(sym):
    ss["nie_tkf"] = sym
    ss["nie_n"] = 12
    ss["goto"] = "newsintel"


# ---------------------------------------------------------------- the page's data, kept ready in the background (warm.py)
_HM_DEFAULT = {False: ("sp500", "1D", "cap"), True: ("sa_all", "1D", "cap")}      # the heat map's first choices


def _compute_lists(sa):
    if sa:
        mv = data.sa_moves()
        return mv, PM.sa_lists(mv)
    mv = PM._universe_moves()
    return mv, {k: PM._list(k, mv) for k in PM.LISTS}


def _compute_heat(sa):
    ukey, period, sizing = _HM_DEFAULT[sa]
    syms = list(tasi.SYMBOLS) if sa else list(SP500)
    df, source = PM.heatmap_frame(ukey, period, sizing, syms=syms)
    if df is None or df.empty:
        return None                                  # not kept: tried again by the next visitor
    return {(ukey, period, sizing): (df, source)}


def _jobs(sa):
    """Everything the page needs, with how long each stays fresh (seconds)."""
    m = MK.SA if sa else MK.US
    jobs = {"tiles": (PM._tile_prices, 120),
            f"snap:{m}": (lambda: PNI.compute_snapshot(m, 24), 240),
            f"stories:{m}": (lambda: PM.top_stories(3, market=m), 240),
            f"lists:{m}": (lambda: _compute_lists(sa), 300),
            f"fg:{m}": (lambda: PI.fg_now(m), 1800),
            f"heat:{m}": (lambda: _compute_heat(sa), 180)}
    if not sa:
        jobs["macro"] = (data.macro, 3600)
    return jobs


def _get(sa, key):
    m = MK.SA if sa else MK.US
    jobs = _jobs(sa)
    k = key if key in jobs else f"{key}:{m}"
    fn, ttl = jobs[k]
    return _timed(f"get {k}", warm.get, k, fn, ttl)


class _Day:
    """What the page's parts share, taken from the data kept ready in the background (warm.py): the news engine's reading,
    the stories, the movers' lists, the mood, the indicators, the heat map, and the companies' logos."""

    def __init__(self, px, sa):
        self.px, self.sa = px, sa
        self._got = {}
        self._lg = None

    def _one(self, key, empty):
        if key not in self._got:
            v = _get(self.sa, key)
            self._got[key] = v if v is not None else empty
        return self._got[key]

    def snap(self):
        return self._one("snap", {})

    def lists(self):
        empty = (pd.DataFrame(), {k: pd.DataFrame() for k in PM.SA_LISTS}) if self.sa else \
            (pd.DataFrame(), {k: (pd.DataFrame(), True) for k in PM.LISTS})
        return self._one("lists", empty)

    def stories(self):
        return self._one("stories", [])

    def fg(self):
        return self._one("fg", None)

    def macro(self):
        return None if self.sa else self._one("macro", None)

    def heat(self):
        pre = self._one("heat", None)
        if pre and self.sa and is_ar():              # made in the background in English: the Saudi names in Arabic
            out = {}
            for k, (df, src) in pre.items():
                df = df.copy()
                m = df["Kind"] == "tadawul"
                df.loc[m, "Name"] = df.loc[m, "Symbol"].map(lambda s_: tasi.name_of(s_, True))
                out[k] = (df, src)
            return out
        return pre

    def lg(self):
        if self._lg is None:
            mv, lists = self.lists()
            if self.sa:
                syms = [s_ for df in lists.values() if not df.empty for s_ in df["Symbol"].head(12)]
            else:
                syms = [s_ for df, _ in lists.values() if not df.empty for s_ in df["Symbol"].head(12)]
            tick = sorted({s_ for n in self.stories() for s_ in n["tickers"]})
            self._lg = data.logos(list(dict.fromkeys(syms + tick)))
        return self._lg


def _top(d):
    ui.header("local_fire_department", "What's trending", "الأكثر رواجاً",
              "The stories moving the market right now, the companies everyone is talking about, and today's biggest moves.",
              "الأخبار اللي تحرّك السوق الحين، والشركات اللي الكل يتكلم عنها، وأكبر تحركات اليوم.")
    snap = d.snap()
    if snap.get("res"):
        ui.html(PNI.breaking_html(snap))
    ui.sec("newspaper", "Top 3 trending stories", "أهم 3 أخبار رائجة")
    stories = d.stories()
    if stories:
        ui.html(PM.stories_html(stories, d.lg(), sa=d.sa))
    else:
        st.caption(L("No trending stories right now.", "لا توجد أخبار رائجة حالياً."))


def _news_and_summary(d):
    snap = d.snap()
    tks = PNI.in_the_news(snap) if snap.get("res") else []
    if tks:
        ui.sec("trending_up", "In the news now", "في الأخبار الحين")
        with st.container(key="nie_tks"):
            cols = st.columns(len(tks))
            for col, (sym, n, net, c) in zip(cols, tks):
                with col:
                    with st.container(key="nie_tk_" + sym):
                        ui.html(PNI.tk_card(sym, n, net, c))
                        st.button(sym, key="nie_tb_" + sym, on_click=_pick_news, args=(sym,), width="stretch")
    ui.sec("summarize", "Market summary", "ملخص السوق")
    mv, lists = d.lists()
    if d.sa:
        ui.html(PM.summary_html_sa(d.px, mv, lists, d.lg()))
    else:
        ui.html(PM.summary_html(PM.summary_data(d.px, mv, lists), d.lg()))


def _movers(d):
    mv, lists = d.lists()
    if d.sa and mv.empty:
        st.info(L("Saudi quotes are unavailable right now. Try again in a minute.", "أسعار السوق السعودي غير متاحة حالياً. حاول بعد دقيقة."))
        return
    ui.sec("leaderboard", "Movers at a glance", "الأسهم الأكثر حركة")
    PM.movers_grid(lists, d.lg(), sa=d.sa, per_row=2)
    with st.container(key="ovmore", horizontal=True, gap="small"):
        st.button(L("Everything trending today", "كل اللي رائج اليوم"), key="ovgo_trend", icon=":material/local_fire_department:",
                  on_click=_open_tool, args=("trend", "trending"))
        st.button(L("All the news", "كل الأخبار"), key="ovgo_news", icon=":material/newspaper:", on_click=_open_tool, args=("news", "news"))


def _mood(snap, v):
    ui.sec("speed", "The market's mood", "مزاج السوق")
    with st.container(key="ovmood"):
        a, b = st.columns(2, gap="medium")
        with a:
            if v is not None:
                ui.ai_note("Fear & Greed", f"{v:.0f}/100")
                ui.html(f'<div class="ovcard" data-nogq><div class="h">{T.icon("speed")}{T.esc(L("Fear & Greed", "الخوف والطمع"))}</div>'
                        f'{T.fg_gauge(v, is_ar(), L("Seven market signals in one score", "سبع إشارات من السوق في درجة واحدة"))}</div>')
            else:
                st.caption(L("The Fear & Greed index is not available right now.", "مؤشر الخوف والطمع غير متاح حالياً."))
            st.button(L("What drives it", "وش يحرّكه"), key="ovgo_fg", icon=":material/speed:", width="stretch",
                      on_click=_open_tool, args=("fg", "sentiment"))
        with b:
            if snap and snap["res"]:
                ui.html(PNI.dial_html(snap["res"], snap["hrs"]))
            else:
                st.caption(L("The news mood is not available right now.", "مزاج الأخبار غير متاح حالياً."))
            st.button(L("Read the news like an analyst", "اقرأ الأخبار مثل المحلل"), key="ovgo_ni", icon=":material/neurology:", width="stretch",
                      on_click=_open_tool, args=("ni", "newsintel"))


def _markets(px, sa, macro=None):
    ui.sec("monitoring", "Markets at a glance", "الأسواق بلمحة")
    groups = PM.SA_TILES if sa else U.MARKET_TILES
    tabs = st.tabs([L(gen, gar) for gen, gar in groups])
    for tab, ((gen, gar), syms) in zip(tabs, groups.items()):
        with tab:
            items = []
            for sym, names in syms.items():
                name = PM._sa_name(sym) if sa else L(*names)
                p, chg, pct = PM._last(px, sym)
                if p is None:
                    items.append(T.tile(name, "—"))
                    continue
                val = f"{p:.3f}%" if gen == "Treasury Yields" else T.fmt_price(p)
                items.append(T.tile(name, val, chg, pct, px[sym]["Close"].tail(22).values, invert=(sym == "^VIX")))
            ui.html(T.tiles(items))
    if not sa:
        if macro is not None:
            _timed("indicators", ui.safe, PM.indicators_section, True, macro)
        else:
            ui.sec("query_stats", "Key economic indicators", "أهم المؤشرات الاقتصادية")
            st.caption(L("The economic indicators are on their way: they show in a moment.", "المؤشرات الاقتصادية في الطريق: تطلع بعد شوي."))


def page_overview():
    sa = MK.is_sa()
    ui.html('<span class="css-anchor"></span>\n' + CSS + PNI.CSS + PNI.CSS2)
    ui.html('<span class="css-anchor"></span>\n' + home.CSS)
    t0 = time.time()
    warm.prefetch(_jobs(sa))                         # every piece the page needs, side by side, in the background
    warm.prefetch(_jobs(not sa), want=False)         # and the other market's, once, so a switch to it opens at once
    px = _get(sa, "tiles") or {}
    PM.ticker_tape(px)
    ui.html(home.top_html(_chips(px, sa)))
    f = _timed("facts", _facts)
    d = _Day(px, sa)
    # the page as a magazine: the news across the page, then each part with tool cards beside it - one on the right, then
    # two on the left, one on the right, two on the left - and the last two side by side at the foot
    with st.container(key="ovpage"):
        _timed("top", ui.safe, _top, d)
        _timed("part a", _with_ads, "a", "right", ["ai"], f, sa, lambda: ui.safe(_news_and_summary, d))
        _timed("part b", _with_ads, "b", "left", ["hunt", "bots"], f, sa, lambda: ui.safe(_movers, d))
        _timed("part c", _with_ads, "c", "right", ["pf", "earn"], f, sa,
               lambda: (_timed("mood", ui.safe, _mood, d.snap(), d.fg()), _timed("heatmap", ui.safe, PM.heatmap_section, d.heat())))
        _timed("part d", _with_ads, "d", "left", ["robo", "academy"], f, sa, lambda: ui.safe(_markets, px, sa, d.macro()))
        last = [k for k in ("xbots", "screener") if _available(k, sa)]
        if last:
            with st.container(key="ovfoot"):
                ui.sec("apps", "More tools to try", "أدوات ثانية تستاهل تجربها")
                with st.container(key="ovads_z"):
                    for k in last:
                        with st.container(key=f"ovad_{k}"):
                            ui.html(_ad_html(k, f, sa, wide=True))
                            st.button(L(*TOOLS[k][4]), key=f"ovgo_{k}", on_click=_open_tool, args=(k, TOOLS[k][0]), width="stretch")
    if sa:
        st.caption(L("Prices from Yahoo Finance (may be delayed). The Saudi market trades Sunday to Thursday, 10 am to 3 pm Riyadh time.",
                     "الأسعار من Yahoo Finance (قد تكون متأخرة). السوق السعودي يتداول من الأحد للخميس، من 10 الصبح لين 3 العصر بتوقيت الرياض."))
    ui.foot()
    if _PROF:
        print(f"[prof] page {'sa' if sa else 'us'} total {time.time() - t0:.2f}s", flush=True)


BUILD = "23.4.7"
