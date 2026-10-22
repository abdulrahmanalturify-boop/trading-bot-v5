"""
p_overview.py - The home page (Overview), the site's first screen since 23.4: the logo and the main prices, then what is
moving the market today, starting with what's trending (the breaking stories, the top three stories, the companies in the
news, the market summary and the movers), the market's mood (fear and greed, the news mood), the heat map and the markets.
The site's tools are cards placed between the parts, like adverts in a magazine (one on the right, two on the left, ...).
Replaces the landing ("Beyond investment") and the old overview.
"""
import os
import re
import time

import streamlit as st

import pandas as pd

import data
import home
import markets as MK
import p_calendar as PC
import p_markets as PM
import p_newsintel as PNI
import theme as T
import mascot
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
    "ai": (None, "auto_awesome", "ai", ("Kuhailan · AI assistant", "كحيلان · المساعد الذكي"), ("Ask Kuhailan anything", "اسأل كحيلان أي شيء"),
           ("A number you don't get, a chart, a word? Ask here and get it in plain words, on any page of the site.",
            "رقم ما فهمته؟ رسم؟ مصطلح؟ اسأل هنا ويشرح لك بكلام بسيط، في أي صفحة بالموقع."), ("Try it now, free", "جرّبه الآن مجاناً")),
    "hunt": ("scanner", "radar", "hunt", ("Today's picks", "فرص اليوم"), ("Don't miss today's opportunity", "لا تفوّت فرصة اليوم"),
             ("The hunter scans the whole market every day and scores every setup out of 100, with entry, stop and target.",
              "الصائد يفحص السوق كله كل يوم ويعطي كل فرصة درجة من 100، مع الدخول والوقف والهدف."), ("See today's picks", "شوف فرص اليوم")),
    "bots": ("paper", "smart_toy", "bots", ("Automation", "أتمتة"), ("Build your bot in a minute", "ابنِ بوتك في دقيقة"),
             ("Pick a strategy, give it virtual money, and watch it trade for you day after day. No code, no risk.",
              "اختر استراتيجية، أعطها فلوس افتراضية، وشوفها تتداول عنك يوم بعد يوم. بدون كود وبدون مخاطرة."), ("Start now, free", "ابدأ الآن مجاناً")),
    "pf": ("pf_dash", "account_balance_wallet", "pf", ("Practice", "تدرّب"), ("Start with virtual money", "ابدأ بفلوس افتراضية"),
           ("Real prices, virtual money: buy and sell like the pros and learn without risking a cent of your own.",
            "أسعار حقيقية وفلوس افتراضية: بِع واشترِ مثل المحترفين وتعلّم بدون ما تخاطر بريال من فلوسك."), ("Open my free portfolio", "افتح محفظتك المجانية")),
    "robo": ("pf_robo", "psychology", "robo", ("Robo Advisor", "المستشار الآلي"), ("Get your portfolio rated, free", "قيّم محفظتك مجاناً"),
             ("Answer a few short questions and get an investment plan built around your goal and how much risk you can take, "
              "then follow it with virtual money and see how it does.",
              "جاوب على كم سؤال قصير وخذ خطة استثمار مبنية على هدفك ومستوى مخاطرتك، ثم تابعها بفلوس افتراضية وشوف كيف تمشي."),
             ("Start my free plan", "ابدأ خطتك المجانية")),
    "academy": ("academy", "school", "academy", ("Learning", "تعلّم"), ("Start studying today", "ابدأ دراستك اليوم"),
                ("From your first share to options: short courses with labs on real charts, at your pace, free.",
                 "من أول سهم إلى الخيارات: دورات قصيرة مع تطبيقات على رسوم حقيقية، على راحتك، ومجاناً."), ("Start studying, free", "ابدأ الدراسة مجاناً")),
    "xbots": ("xbots", "alternate_email", "x", ("Social signals", "إشارات X"), ("Who reads X right?", "مين يقرأ X صح؟"),
              ("Five bots read X every hour and trade on the crowd's mood. Follow the log and see which one gets it right.",
               "خمس بوتات تقرأ X كل ساعة وتتداول على مزاج الناس. تابع السجل وشوف مين فيها يصيب."), ("Meet the bots", "تعرّف عليها")),
    "screener": ("screener", "filter_alt", "scr", ("Research", "بحث"), ("Find your stock in a minute", "لقّ سهمك في دقيقة"),
                 ("Hundreds of companies, a few filters, and the ones that fit you are in front of you.",
                  "مئات الشركات وكم فلتر، والأسهم اللي تناسبك قدامك."), ("Try the screener", "جرّب الفلتر")),
}


CSS = """<style data-lm="keep">
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600&display=swap');
/* ---- a part of the page with its tool cards beside it: the cards stay in view while that part is read */
[data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"] > div[class*="st-key-ovads_"]),
[data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] div[class*="st-key-ovads_"]){align-items:flex-start!important}
[data-testid="stColumn"]:has(div[class*="st-key-ovads_"]){position:sticky;top:80px;align-self:flex-start;z-index:2}
div[class*="st-key-ovads_"]{gap:16px!important;padding-top:18px}
div[class*="st-key-ovbody_"] .msg{grid-template-columns:repeat(2,minmax(0,1fr))!important}
div.st-key-ovsum .msg{grid-template-columns:repeat(2,minmax(0,1fr))!important}
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
.ovad .big svg.xlg{width:118px;height:118px;margin:6px}
.ovad .k .ic svg.xlg{width:17px;height:17px;margin:0;color:#fff}
div[class*="st-key-ovad_"]:hover .ovad .big,.ovad.solo:hover .big{transform:rotate(-2deg) scale(1.08)}
.ovad .k{display:flex;align-items:center;justify-content:space-between;gap:8px;font-size:10.5px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.8)}
.ovad.rtl .k{letter-spacing:0;font-size:11.5px}
.ovad .k>span{display:inline-flex;align-items:center;gap:8px}
.ovad .k .ic{width:28px;height:28px;border-radius:9px;display:grid;place-items:center;background:rgba(255,255,255,.18);box-shadow:inset 0 1px 0 rgba(255,255,255,.22)}
.ovad .k .ic .ms{font-size:17px;color:#fff}
.ovad .k .ic svg.khl{width:26px;height:26px;animation:none}
.vz.chat .a i svg.khl{width:22px;height:22px;animation:none}
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
.vz.chat .a i{flex:none;width:24px;height:24px;border-radius:50%;display:grid;place-items:center;font-style:normal;font-size:10px;background:linear-gradient(155deg,#7B6CFF,#3B82F6 58%,#2DB6EB)}
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
.vz.donut .lgn{display:grid;grid-template-columns:1fr 1fr;gap:6px 10px;font-size:11.5px}
.vz.donut .lgn span{display:flex;align-items:center;gap:6px}
.vz.donut .lgn i{width:9px;height:9px;border-radius:3px}
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
.ovad.wide.news .bd{grid-template-columns:minmax(0,1.5fr) minmax(0,1fr)}
/* the earnings card under an advert */
.ovearnh{display:flex;align-items:center;gap:8px;margin:2px 4px 8px;font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#8E97AD}
.ovearnh .ms{font-size:17px}
.ehub.one{grid-template-columns:1fr!important;margin:0!important}
.ehub.one .day{border-radius:18px}
div.st-key-ovearn [data-testid="stButton"] button{min-height:34px!important;border-radius:999px!important;font-size:12.5px!important}
/* the mood row: the two dials side by side, the same height */
.ovcard{box-sizing:border-box;margin-top:4px;padding:14px 14px 10px;border-radius:18px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08)}
.ovcard .h{display:flex;align-items:center;gap:8px;font-size:13px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#C9C4D3;margin-bottom:6px}
.ovcard .h .ms{font-size:18px}
div.st-key-ovmore [data-testid="stButton"] button{border-radius:999px!important}
div.st-key-ovfoot{margin-top:8px}
div[class*="st-key-ovads_z"]{flex-direction:row!important;gap:22px!important;padding-top:0;margin-bottom:22px}
div[class*="st-key-ovads_z"]>*{flex:1 1 0!important;min-width:0!important}
.vz.rate{display:grid;grid-template-columns:104px minmax(0,1fr);gap:14px;padding:12px 14px;box-sizing:border-box;height:auto!important;align-items:center}
.vz.rate .sc{display:flex;flex-direction:column;align-items:center;gap:6px}
.vz.rate .ring{position:relative;width:88px;height:88px}.vz.rate .ring svg{width:100%;height:100%}
.vz.rate .num{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;line-height:1}
.vz.rate .num b{font-size:26px;font-weight:800}.vz.rate .num span{font-size:9.5px;opacity:.75;margin-top:2px}
.vz.rate .gr{display:flex;align-items:center;gap:6px;font-size:12.5px;font-weight:700}
.vz.rate .gr i{font-style:normal;width:20px;height:20px;border-radius:6px;display:grid;place-items:center;font-size:11px;font-weight:800;background:#A7F3D0;color:#064E3B}
.vz.rate small{font-size:10px;opacity:.65}
.vz.rate .fs{display:flex;flex-direction:column;gap:7px;min-width:0}
.vz.rate .f .t{display:flex;align-items:center;gap:6px;font-size:11.5px;font-weight:700}
.vz.rate .f .t .ms{font-size:14px;opacity:.9}.vz.rate .f .t b{margin-inline-start:auto;font-size:11.5px}
.vz.rate .bar{height:5px;margin-top:3px;border-radius:9px;background:rgba(255,255,255,.16);overflow:hidden}
.vz.rate .bar i{display:block;height:100%;border-radius:9px}
/* ---- the Robo Advisor banner across the page, after the owner's design: the site's own colours (navy, violet, cyan) */
div.st-key-ovad_robo{margin:10px 0 6px}
.ovad.banner.rb{padding:28px 30px 26px;border-radius:26px;color:#fff;
  background:radial-gradient(70% 90% at 0% 0%,rgba(123,69,240,.35),transparent 60%),radial-gradient(60% 80% at 100% 100%,rgba(45,182,235,.22),transparent 60%),linear-gradient(135deg,#17122B,#1A1540 55%,#0F2742);
  border:1px solid rgba(255,255,255,.12);box-shadow:0 1px 0 rgba(255,255,255,.12) inset,0 24px 50px -30px rgba(59,139,235,.6)}
.ovad.banner.rb::after{display:none}
.ovad.banner.rb .bd{display:grid;grid-template-columns:minmax(0,.9fr) minmax(0,1.6fr);gap:28px;align-items:center}
.rb .rbkk{display:flex;align-items:center;gap:8px;font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:#2DB6EB}
.rb .rbkk b{font-size:17px;letter-spacing:.1em;color:#fff}.rb .rbkk span{color:rgba(255,255,255,.35)}.rb .rbkk em{font-style:normal;color:#9FD9F2}
.rb.rtl .rbkk{letter-spacing:0}.rb.rtl .rbkk em{font-size:12px}
.rb h3{font-family:"Playfair Display",Georgia,"Times New Roman",serif;font-weight:500;font-size:36px;line-height:1.08;letter-spacing:-.015em;margin:14px 0 12px;color:#fff}
.rb.rtl h3{font-family:Almarai,sans-serif;font-weight:800;font-size:34px;line-height:1.25}
.rb p{font-size:14.5px;line-height:1.6;color:rgba(255,255,255,.82);margin:0 0 14px;max-width:46ch}
.rb .rbchips{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 16px}
.rb .rbchips span{display:inline-flex;align-items:center;gap:6px;padding:7px 12px;border-radius:11px;font-size:12.5px;font-weight:700;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.14)}
.rb .rbchips .ms{font-size:16px;color:#2DB6EB}
.rb .rbcta{display:flex;align-items:center;flex-wrap:wrap;gap:8px 18px;margin:0 0 14px}
.rb .rbcta .go{width:auto;padding:12px 20px;font-size:14.5px;border-radius:14px;color:#17122B;background:linear-gradient(135deg,#fff,#DDEBFF)}
.rb .rbcta .rblnk{display:inline-flex;align-items:center;gap:6px;font-size:14px;font-weight:700;color:#9FD9F2}
.rb .rbcta .rblnk .ms{font-size:18px;transition:transform .25s}.rb.rtl .rbcta .rblnk .ms{transform:scaleX(-1)}
div[class*="st-key-ovad_"]:hover .rb .cta .lnk .ms{transform:translateX(4px)}div[class*="st-key-ovad_"]:hover .rb.rtl .cta .lnk .ms{transform:scaleX(-1) translateX(4px)}
.rb .rbfacts{font-size:11.5px;letter-spacing:.06em;color:rgba(255,255,255,.6)}
.rb .rbpic{display:flex;flex-direction:column;gap:12px;min-width:0}
.rb .rbsteps{display:grid;grid-template-columns:minmax(0,1.25fr) 18px minmax(0,1fr) 18px minmax(0,1fr);gap:6px;align-items:stretch}
.rb .rbarr{align-self:center;color:rgba(255,255,255,.45);width:18px;overflow:hidden;text-align:center}.rb .rbarr .ms{font-size:18px}.rb.rtl .rbarr .ms{transform:scaleX(-1)}
.rb .rbcard,.rb .rbstrip{position:relative;border-radius:18px;padding:14px 14px 12px;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.14);box-shadow:inset 0 1px 0 rgba(255,255,255,.08);min-width:0}
.rb .rbcard small,.rb .rbstrip .rbrt small{position:absolute;bottom:8px;inset-inline-end:12px;font-size:9.5px;color:rgba(255,255,255,.45)}
.rb .rbcard .rbh{display:flex;align-items:flex-start;gap:9px;margin-bottom:10px}
.rb .rbcard .rbh b{flex:none;width:24px;height:24px;border-radius:50%;display:grid;place-items:center;font-size:12px;font-weight:800;background:linear-gradient(135deg,#2DB6EB,#7B45F0);color:#fff}
.rb .rbcard .rbn{display:block;font-size:13.5px;font-weight:800;line-height:1.2}.rb .rbcard .rbd{display:block;font-size:11px;line-height:1.45;color:rgba(255,255,255,.7);margin-top:2px}
.rb .rbhs{display:grid;grid-template-columns:78px minmax(0,1fr);gap:10px;align-items:center;padding-bottom:12px}
.rb .rbhs .rbsc{display:flex;flex-direction:column;align-items:center;gap:6px}
.rb .rbhs .rbring{position:relative;width:78px;height:78px}.rb .rbhs .rbring svg{display:block;width:78px;height:78px}
.rb .rbhs .rbnum{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;line-height:1}
.rb .rbhs .rbnum b{font-size:24px;font-weight:800}.rb .rbhs .rbnum span{font-size:9.5px;opacity:.7;margin-top:3px}
.rb .rbhs .rbgr{display:flex;align-items:center;gap:6px;font-size:12.5px;font-weight:700}
.rb .rbhs .rbgr i{font-style:normal;width:20px;height:20px;border-radius:6px;display:grid;place-items:center;font-size:11px;font-weight:800;background:#F87171;color:#2A0A0A}
.rb .rbhs .rbfs{display:flex;flex-direction:column;gap:6px;min-width:0}
.rb .rbhs .rbf .rbt{display:flex;align-items:center;gap:5px;font-size:10.5px;font-weight:700;white-space:nowrap}
.rb .rbhs .rbf .rbt .ms{display:none}.rb .rbhs .rbf .rbt b{margin-inline-start:auto;font-size:11px}
.rb .rbhs .rbbar{height:4px;margin-top:3px;border-radius:9px;background:rgba(255,255,255,.14);overflow:hidden}.rb .rbhs .rbbar i{display:block;height:100%;border-radius:9px}
.rb .rbrk{display:block;width:100%;height:auto;margin:6px 0 2px}.rb.rtl .rbrk{transform:scaleX(-1)}
.rb .rbrkl{display:flex;justify-content:space-between;font-size:10.5px;color:rgba(255,255,255,.7);padding-bottom:12px}
.rb .rbpl{display:flex;align-items:center;gap:10px;padding:4px 0 12px}
.rb .rbpl svg{flex:none;width:66px;height:66px}
.rb .rbpl .rblg{display:flex;flex-direction:column;gap:6px;font-size:11px;min-width:0}
.rb .rbpl .rblg span{display:flex;align-items:center;gap:7px}.rb .rbpl .rblg i{width:9px;height:9px;border-radius:3px;flex:none}.rb .rbpl .rblg b{margin-inline-start:auto;font-weight:800}
.rb .rbstrip{display:grid;grid-template-columns:minmax(0,1.3fr) repeat(5,minmax(0,1fr));gap:8px;align-items:center;padding:12px 14px}
.rb .rbstrip .rbw .rbn{display:block;font-size:14px;font-weight:800}.rb .rbstrip .rbw .rbd{display:block;font-size:11px;color:rgba(255,255,255,.7);margin-top:3px;line-height:1.4}
.rb .rbstrip .rbrt{position:relative;display:flex;flex-direction:column;align-items:center;gap:5px;padding-bottom:12px}
.rb .rbstrip .rbrt .rbl{font-size:10px;font-weight:700;color:rgba(255,255,255,.75);text-align:center;line-height:1.2}
.rb .rbstrip .rbrg{position:relative;width:54px;height:54px;display:grid;place-items:center}.rb .rbstrip .rbrg svg{position:absolute;inset:0}.rb .rbstrip .rbrg b{font-size:14px;font-weight:800}
.rb .rbstrip .rbrt small{inset-inline-end:auto;left:50%;transform:translateX(-50%);bottom:0}
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
  .ovad.banner.rb{padding:20px 16px}.ovad.banner.rb .bd{grid-template-columns:1fr;gap:18px}.rb h3{font-size:30px}.rb.rtl h3{font-size:26px}
  .rb .rbsteps{grid-template-columns:1fr}.rb .rbarr{display:none}.rb .rbstrip{grid-template-columns:repeat(3,minmax(0,1fr))}.rb .rbstrip .rbw{grid-column:1/-1}
  div[class*="st-key-ovbody_"] .msg{grid-template-columns:minmax(0,1fr)!important}
}
@container ovp (max-width:520px){div[class*="st-key-ovads_"]>*{flex-basis:84%!important;min-width:84%!important}}
/* the live numbers on a tile: pills in the kicker row and inside the picture */
.ovad .k .lv{display:inline-flex;align-items:center;gap:5px;padding:3px 9px;border-radius:999px;background:rgba(5,8,25,.3);border:1px solid rgba(255,255,255,.2);font-size:10.5px;letter-spacing:.04em;text-transform:none;color:#fff}
.ovad .k .lv i{width:6px;height:6px;border-radius:50%;background:#4ADE80;animation:ovlive 1.8s infinite}
.vz.picks{display:flex;flex-direction:column;justify-content:center;gap:4px;padding:8px 10px;box-sizing:border-box;height:auto!important}
.vz.picks .r{display:grid;grid-template-columns:30px minmax(0,1fr) 38px;gap:9px;align-items:center;padding:5px 6px;border-radius:12px;transition:background .2s}
.vz.picks .r:hover{background:rgba(255,255,255,.08)}
.vz.picks .lg{width:30px;height:30px;border-radius:9px;overflow:hidden;background:rgba(255,255,255,.12);display:grid;place-items:center;font-size:11px;font-weight:800}
.vz.picks .lg img{width:100%;height:100%;object-fit:cover}
.vz.picks .nm{min-width:0}.vz.picks .nm b{display:block;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.vz.picks .nm span{display:block;font-size:11px;color:rgba(255,255,255,.72);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.vz.picks .nm em{font-style:normal;font-weight:700;color:#BAE6FD}
.vz.picks .su{font-size:10.5px;font-weight:700;padding:3px 8px;border-radius:999px;background:rgba(255,255,255,.14);white-space:nowrap}
.vz.picks .sc{display:grid;place-items:center;position:relative;width:38px;height:38px}
.vz.picks .sc svg{position:absolute;inset:0;width:100%;height:100%;transform:rotate(-90deg)}
.vz.picks .sc b{font-size:11.5px;line-height:1}.vz.picks .sc small{font-size:8.5px;opacity:.8;line-height:1}
.vz.picks .sc .g{display:flex;flex-direction:column;align-items:center}
.vz.picks .more{text-align:center;font-size:11px;color:rgba(255,255,255,.75);padding:4px 0 2px}
.vz.stat{display:flex;flex-direction:column;justify-content:center;gap:8px;padding:12px 14px;box-sizing:border-box;height:auto!important;min-height:118px}
.vz.stat .big{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}
.vz.stat .big b{font-size:26px;font-weight:800;letter-spacing:-.01em;direction:ltr}
.vz.stat .big .pill,.vz.stat .pill{font-size:12px}
.vz.stat .l{font-size:11px;color:rgba(255,255,255,.75)}
.vz.stat .row{display:flex;justify-content:space-between;gap:10px;font-size:12px;color:rgba(255,255,255,.9);border-top:1px solid rgba(255,255,255,.12);padding-top:7px}
.vz.stat .row b{font-weight:800}
.vz.fgm{display:flex;flex-direction:column;justify-content:center;gap:8px;padding:12px 14px;box-sizing:border-box;height:auto!important;min-height:118px}
.vz.fgm .top{display:flex;align-items:baseline;justify-content:space-between;gap:10px}
.vz.fgm .top b{font-size:30px;font-weight:800;line-height:1}
.vz.fgm .top span{font-size:12.5px;font-weight:700;padding:3px 10px;border-radius:999px;background:rgba(255,255,255,.92);color:#1E1B4B}
.vz.fgm .bar{position:relative;height:10px;border-radius:999px;background:linear-gradient(90deg,#EF4444,#F59E0B,#FDE68A,#86EFAC,#22C55E)}
.ovad.rtl .vz.fgm .bar{background:linear-gradient(270deg,#EF4444,#F59E0B,#FDE68A,#86EFAC,#22C55E)}
.vz.fgm .bar i{position:absolute;top:-4px;width:18px;height:18px;margin-inline-start:-9px;border-radius:50%;background:#fff;border:3px solid #1E1B4B;box-shadow:0 2px 6px rgba(0,0,0,.4)}
.vz.fgm .zs{display:flex;justify-content:space-between;font-size:9.5px;color:rgba(255,255,255,.7)}
.vz.story{display:flex;flex-direction:column;justify-content:center;gap:6px;padding:11px 13px;box-sizing:border-box;height:auto!important;min-height:118px}
.vz.story .s{padding:6px 0;border-top:1px solid rgba(255,255,255,.12)}.vz.story .s:first-child{border-top:0;padding-top:0}
.vz.story .t{font-size:12.5px;font-weight:700;line-height:1.4;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.vz.story .m{display:flex;align-items:center;gap:8px;font-size:11px;color:rgba(255,255,255,.75)}
.vz.story .m .sc{font-weight:800;padding:2px 7px;border-radius:7px;background:rgba(255,255,255,.92);color:#1E1B4B}
.vz.story .m .ms{font-size:14px}
.vz.fgm .row{display:flex;justify-content:space-between;gap:10px;font-size:12px;border-top:1px solid rgba(255,255,255,.12);padding-top:7px;margin-top:2px}
.vz.days{display:grid;grid-template-columns:repeat(5,1fr);gap:4px;padding:10px 8px;box-sizing:border-box;height:auto!important;min-height:74px}
.vz.days span{display:flex;flex-direction:column;align-items:center;gap:4px;padding:6px 2px;border-radius:9px;background:rgba(255,255,255,.1)}
.vz.days b{font-size:10px}.vz.days i{font-style:normal;font-size:6px;letter-spacing:1px;color:#A5B4FC;line-height:1}
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
    }.get(key, [])


# ---------------------------------------------------------------- each card's picture (drawn, no made-up numbers)
def _vz(key, f):
    ar = is_ar()
    if key == "ai":
        q = L("What does RSI mean?", "وش يعني مؤشر RSI؟")
        a = L("A momentum gauge from 0 to 100: above 70 the stock may be overbought, under 30 oversold.",
              "مقياس زخم من 0 إلى 100: فوق 70 ممكن يكون السهم متشبّع شراء، وتحت 30 متشبّع بيع.")
        return (f'<div class="vz chat"><div class="q">{T.esc(q)}</div><div class="a"><i>{mascot.svg(22, uid="kc")}</i><span>{T.esc(a)}</span></div>'
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
        return f'<div class="vz donut"><svg viewBox="0 0 100 100" aria-hidden="true">{arcs}</svg><div class="lgn">{leg}</div></div>'
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


def _kick_pill(key, live):
    """What sits at the end of the kicker row: a live number when there is one, else "Free"."""
    if key == "hunt" and live:
        n_opp = live["opp"]
        return f'<span class="lv"><i></i>{T.esc(L(f"{n_opp} opportunities today", f"{n_opp} فرصة اليوم"))}</span>'
    if key == "bots" and live:
        n_b = live["n"]
        en_b = f"{n_b} bot live" if n_b == 1 else f"{n_b} bots live"
        ar_b = "بوت شغّال" if n_b == 1 else f"{n_b} بوتات شغّالة"
        return f'<span class="lv"><i></i>{T.esc(L(en_b, ar_b))}</span>'
    return f'<em>{T.esc(L("Free", "مجاني"))}</em>'


def _ad_html(key, d, f, sa, wide=False):
    page, icon, tone, kick, title, pitch, cta = (TOOLS.get(key) or TILES[key])
    ar = is_ar()
    solo = key == "ai"
    attrs = ' data-open-ai="1" role="button" tabindex="0"' if solo else ""
    vz, live = _live_vz(key, d, f, sa)
    xs = T.xify if key == "xbots" else T.esc          # the X bots' texts: the letter X drawn as X's logo
    pts = "".join(f'<li>{T.icon("check_circle")}<span>{xs(x)}</span></li>' for x in _points(key, f, sa))
    text = (f'<div class="tx"><b class="tt">{xs(L(*title))}</b><p>{xs(L(*pitch))}</p>{"<ul>" + pts + "</ul>" if pts else ""}'
            f'<span class="go">{T.esc(L(*cta))}{T.icon("arrow_forward")}</span></div>')
    return (f'<div class="ovad {tone}{" rtl" if ar else ""}{" solo" if solo else ""}{" wide" if wide else ""}" data-nogq{attrs}>'
            f'<span class="big" aria-hidden="true">{T.xlogo() if key == "xbots" else icon}</span>'
            f'<div class="k"><span><span class="ic">{mascot.svg(26, uid="ka") if solo else T.xlogo() if key == "xbots" else T.icon(icon)}</span>{xs(L(*kick))}</span>{_kick_pill(key, live)}</div>'
            f'<div class="bd">{vz}{text}</div></div>')


def _ring(v, size=54, col="#5EEAD4", width=5, track="rgba(255,255,255,.14)"):
    r = size / 2 - width
    circ = 2 * 3.14159 * r
    return (f'<svg viewBox="0 0 {size} {size}" width="{size}" height="{size}" aria-hidden="true"><circle cx="{size / 2}" cy="{size / 2}" r="{r:.1f}" fill="none" stroke="{track}" stroke-width="{width}"/>'
            f'<circle cx="{size / 2}" cy="{size / 2}" r="{r:.1f}" fill="none" stroke="{col}" stroke-width="{width}" stroke-linecap="round" '
            f'stroke-dasharray="{circ * v / 100:.1f} {circ:.1f}" transform="rotate(-90 {size / 2} {size / 2})"/></svg>')


def _banner_html(key, d, f, sa):
    """The Robo Advisor as a banner across the page, after the owner's design: on one side the headline, the promise, two chips,
    the calls to action and the facts; on the other three step cards - the portfolio's health (its score and what makes it), the
    risk, the plan - and under them a strip of the five ratings. Every number is a sample, marked as one."""
    ar = is_ar()
    nq = f["questions"] or 13
    smp = T.esc(L("Sample", "مثال"))
    # 1 · the portfolio's health (the portfolio page's card, in small)
    facs = [("hub", L("Diversification", "التنويع"), 65, L("3 positions · 2 sectors", "3 مراكز · قطاعان")),
            ("pie_chart", L("Concentration", "التركيز"), 38, L("Largest: MRNA 53.9%", "الأكبر: MRNA 53.9%")),
            ("shield", L("Protection", "الحماية"), 20, L("1 of 3 with a stop", "1 من 3 عليه وقف")),
            ("speed", L("Risk", "المخاطرة"), 0, L("Leverage 1.28× · swings 82%/yr", "رافعة 1.28× · تذبذب 82%/سنة")),
            ("trending_up", L("Against the market", "مقابل السوق"), 57, L("+1.2% vs S&P 500 −0.6%", "+1.2% مقابل S&P 500 −0.6%"))]
    col = lambda v: "#4ADE80" if v >= 75 else "#2DB6EB" if v >= 55 else "#F5B94A" if v >= 40 else "#F87171"
    rows = "".join(f'<div class="rbf"><div class="rbt">{T.icon(ic)}<span>{T.esc(n)}</span><b>{v}</b></div>'
                   f'<div class="rbbar"><i style="width:{max(v, 2)}%;background:{col(v)}"></i></div></div>' for ic, n, v, _ in facs)
    health = (f'<div class="rbhs"><div class="rbsc"><div class="rbring">{_ring(36, 78, "#F87171", 6)}<div class="rbnum"><b>36</b><span>/ 100</span></div></div>'
              f'<div class="rbgr"><i>E</i>{T.esc(L("At risk", "في خطر"))}</div></div><div class="rbfs">{rows}</div></div>')
    c1 = (f'<div class="rbcard"><div class="rbh"><b>1</b><div><span class="rbn">{T.esc(L("Your portfolio health", "صحة محفظتك"))}</span>'
          f'<span class="rbd">{T.esc(L("Your score, and what makes it.", "درجتك، ووش يصنعها."))}</span></div></div>{health}<small>{smp}</small></div>')
    # 2 · the risk: a curve with the marker on moderate risk
    curve = ('<svg viewBox="0 0 220 70" aria-hidden="true" class="rbrk"><defs><linearGradient id="rbg" x1="0" x2="1"><stop offset="0" stop-color="#2DB6EB"/><stop offset="1" stop-color="#7B45F0"/></linearGradient></defs>'
             '<path d="M6 54 C 50 54, 70 16, 110 16 S 170 54, 214 54" fill="none" stroke="url(#rbg)" stroke-width="3" stroke-linecap="round"/>'
             '<circle cx="110" cy="16" r="8" fill="#fff" stroke="#7B45F0" stroke-width="3"/><circle cx="6" cy="54" r="3.5" fill="#2DB6EB"/><circle cx="214" cy="54" r="3.5" fill="#7B45F0"/></svg>')
    c2 = (f'<div class="rbcard"><div class="rbh"><b>2</b><div><span class="rbn">{T.esc(L("Your risk", "مخاطرتك"))}</span>'
          f'<span class="rbd">{T.esc(L("Share your comfort with ups and downs.", "قول لنا قد إيش تتحمل الصعود والهبوط."))}</span></div></div>'
          f'{curve}<div class="rbrkl"><span>{T.esc(L("Lower risk", "مخاطرة أقل"))}</span><span>{T.esc(L("Moderate risk", "مخاطرة متوسطة"))}</span><span>{T.esc(L("Higher risk", "مخاطرة أعلى"))}</span></div><small>{smp}</small></div>')
    # 3 · the plan: a donut and its legend
    segs = [("#2DB6EB", 60, L("Stocks", "أسهم")), ("#7B45F0", 25, L("Bonds", "سندات")), ("#F5B94A", 10, L("Cash", "كاش")), ("#A78BFA", 5, L("Other", "أخرى"))]
    circ, off, arcs = 2 * 3.14159 * 34, 0.0, ""
    for c_, pc, _ in segs:
        ln = circ * pc / 100
        arcs += (f'<circle cx="50" cy="50" r="34" fill="none" stroke="{c_}" stroke-width="12" stroke-dasharray="{ln - 2:.1f} {circ - ln + 2:.1f}" '
                 f'stroke-dashoffset="{-off:.1f}" transform="rotate(-90 50 50)"/>')
        off += ln
    leg = "".join(f'<span><i style="background:{c_}"></i>{T.esc(n)}<b>{pc}%</b></span>' for c_, pc, n in segs)
    c3 = (f'<div class="rbcard"><div class="rbh"><b>3</b><div><span class="rbn">{T.esc(L("Your plan", "خطتك"))}</span>'
          f'<span class="rbd">{T.esc(L("Get a personalized plan you can follow with virtual money.", "خذ خطة مخصصة لك تتابعها بفلوس افتراضية."))}</span></div></div>'
          f'<div class="rbpl"><svg viewBox="0 0 100 100" aria-hidden="true">{arcs}</svg><div class="rblg">{leg}</div></div><small>{smp}</small></div>')
    arrow = f'<i class="rbarr">{T.icon("arrow_forward")}</i>'
    # the strip of ratings
    rates = [(L("Diversification", "التنويع"), 78), (L("Concentration", "التركيز"), 42), (L("Protection", "الحماية"), 71), (L("Risk", "المخاطرة"), 56),
             (L("Against the market", "مقابل السوق"), 69)]
    rr = "".join(f'<div class="rbrt"><span class="rbl">{T.esc(n)}</span><div class="rbrg">{_ring(v, 54, col(v), 5)}<b>{v}</b></div><small>{smp}</small></div>' for n, v in rates)
    strip = (f'<div class="rbstrip"><div class="rbw"><span class="rbn">{T.esc(L("Your portfolio rating", "تقييم محفظتك"))}</span>'
             f'<span class="rbd">{T.esc(L("See how your portfolio scores across key areas.", "شوف درجات محفظتك في النواحي المهمة."))}</span></div>{rr}</div>')
    # the words
    head = L("From your goals to your next move.", "من أهدافك إلى خطوتك الجاية.")
    sub = L("Rate your portfolio. Build a plan around your goals and risk. Follow it with virtual money.",
            "قيّم محفظتك. ابنِ خطة حول أهدافك ومخاطرتك. تابعها بفلوس افتراضية.")
    chips = (f'<span>{T.icon("description")}{T.esc(L("Personalized plan", "خطة مخصصة"))}</span>'
             f'<span>{T.icon("bar_chart")}{T.esc(L("Virtual portfolio", "محفظة افتراضية"))}</span>')
    facts = " • ".join(T.esc(x) for x in (L("Free", "مجاني"), L(f"{nq} short questions", f"{nq} سؤال قصير"), L("No sign-up", "بدون تسجيل"), L("Two minutes", "دقيقتين")))
    return (f'<div class="ovad banner rb{" rtl" if ar else ""}" data-nogq><div class="bd">'
            f'<div class="tx"><div class="rbkk"><b>TURA</b><span>|</span><em>{T.esc(L("Robo Advisor", "المستشار الآلي"))}</em></div>'
            f'<h3>{T.esc(head)}</h3><p>{T.esc(sub)}</p><div class="rbchips">{chips}</div>'
            f'<div class="rbcta"><span class="go">{T.esc(L("Explore my portfolio", "استكشف محفظتي"))}{T.icon("arrow_forward")}</span>'
            f'<span class="rblnk">{T.esc(L("Build my plan", "ابنِ خطتي"))}{T.icon("arrow_forward")}</span></div>'
            f'<div class="rbfacts">{facts}</div></div>'
            f'<div class="rbpic"><div class="rbsteps">{c1}{arrow}{c2}{arrow}{c3}</div>{strip}</div></div></div>')


def _open_tool(key, page):
    if key == "bots":                               # the visitor's own bots, the new bot's form open (p_paper)
        ss["pb_view"] = "mine"
        ss["pb_build"] = True
    ss["goto"] = page


def _available(key, sa):
    page = (TOOLS.get(key) or TILES.get(key) or (None,))[0]
    if key == "earn":
        return not sa
    return (key in TOOLS or key in TILES) and (page is None or not sa or page in MK.SA_PAGES)


PROMO = ("hunt", "bots", "xbots")                 # the cards drawn by promo.py (the Trading Bot menu's pages)


def _card(key, d, f, sa, wide=False):
    if key == "earn":                               # the next session's earnings (a card of the earnings calendar)
        with st.container(key="ovearn"):
            got = _timed("earnings", ui.safe, PC.next_session_html, 8)
            if got:
                ui.html(f'<div class="ovearnh">{T.icon("event_upcoming")}{T.esc(L("Earnings next session", "أرباح الجلسة الجاية"))}</div>' + got)
                st.button(L("Earnings calendar", "مواعيد الأرباح"), key="ovgo_earn", icon=":material/event_upcoming:", width="stretch",
                          on_click=_open_tool, args=("earn", "earnings"))
        return
    if key == "ai":                                 # the chat window opens on the page (theme.FX_JS presses the AI button)
        ui.html(_ad_html(key, d, f, sa, wide))
        return
    tool = TOOLS.get(key) or TILES[key]
    with st.container(key=f"ovad_{key}"):
        if key in PROMO:                            # the Trading Bot pages: the interactive cards of promo.py
            import promo
            mk = MK.SA if sa else MK.US
            live = d.hunt() if key == "hunt" else d.bots() if key == "bots" else d.xb()
            ui.html(promo.CSS + promo.card_html(key, tool, f, live, mk, sa, wide))
        else:
            ui.html(_ad_html(key, d, f, sa, wide))
        st.button(L(*tool[4]), key=f"ovgo_t_{key}", on_click=_open_tool, args=(key, tool[0]), width="stretch")


def _banner(key, d, f, sa):
    """A tool across the whole page (the Robo Advisor); the whole banner opens it."""
    if not _available(key, sa):
        return
    with st.container(key=f"ovad_{key}"):
        ui.html(_banner_html(key, d, f, sa))
        st.button(L(*TOOLS[key][4]), key=f"ovgo_t_{key}", on_click=_open_tool, args=(key, TOOLS[key][0]), width="stretch")


def _with_ads(tag, side, keys, d, f, sa, body):
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
                _card(k, d, f, sa)
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


# ---------------------------------------------------------------- the tools first: the live numbers each tile shows
def _compute_hunt(sa):
    """Today's picks: the last hunt made in this server (by a visitor of the Opportunity Hunter, which keeps it 15 minutes) - the
    home page never runs the hunter itself (hundreds of price histories: too much for the server and for Yahoo); None until then."""
    import p_scanner as PS
    m = MK.SA if sa else MK.US
    got = None
    for key in (("sa_all", "sa_top") if sa else ("top", "sp500", "dow")):
        got = PS.LAST_HUNT.get((key, m))
        if got:
            break
    res = got.get("res") if got else None
    if res is None or res.empty:
        return None
    top = res.sort_values("Score", ascending=False).head(4)
    picks = [{"sym": r["Symbol"], "name": str(r["Name"]), "score": float(r["Score"]), "grade": str(r["Grade"]), "setup": str(r["Setup"]),
              "status": str(r["Status"]), "entry": r.get("Entry"), "stop": r.get("Stop"), "target": r.get("Target")} for _, r in top.iterrows()]
    return {"n": int(got["n"]), "opp": int((res["Score"] >= 65).sum()), "a": int((res["Score"] >= 75).sum()),
            "fresh": int((res["Status"] == "fresh").sum()), "time": got["time"], "picks": picks, "reg": got.get("reg")}


def _bots_live(mk):
    """The site's bots as last replayed (kept by p_paper): total balance, the best one, open trades; None until a replay exists."""
    try:
        import paperbots as PB
        import p_paper as PP
        bots = PB.list_bots(mk, "site")
        if not bots:
            return None
        hit = PB.last_all(bots)
        if not hit:
            return None
        sims = hit[0]
        live = [x for x in sims if x["ok"] and not x["waiting"]]
        if not live:
            return {"n": len(bots)}
        cap = sum(x["bot"]["capital"] for x in live)
        bal = sum(x["final"] for x in live)
        best = PP.ranked(sims)[0]
        return {"n": len(bots), "bal": bal, "ret": (bal / cap - 1) * 100 if cap else 0.0, "open": sum(x["n_open"] for x in live),
                "best": best["bot"]["name"], "best_ret": best.get("ret") or 0.0}
    except Exception:
        return None


def _fg_label(v):
    if v < 25:
        return L("Extreme fear", "خوف شديد")
    if v < 45:
        return L("Fear", "خوف")
    if v <= 55:
        return L("Neutral", "محايد")
    if v <= 75:
        return L("Greed", "طمع")
    return L("Extreme greed", "طمع شديد")


def _ring_html(score, grade):
    from p_scanner import GRADE_COLOR, _C
    col = GRADE_COLOR.get(grade, _C)
    r, circ = 16, 2 * 3.14159 * 16
    return (f'<span class="sc"><svg viewBox="0 0 38 38"><circle cx="19" cy="19" r="{r}" fill="none" stroke="rgba(255,255,255,.2)" stroke-width="3.5"/>'
            f'<circle cx="19" cy="19" r="{r}" fill="none" stroke="{col}" stroke-width="3.5" stroke-linecap="round" stroke-dasharray="{circ * score / 100:.1f} {circ:.1f}"/></svg>'
            f'<span class="g"><b style="color:{col}">{T.esc(grade)}</b><small>{score:.0f}</small></span></span>')


def _live_vz(key, d, f, sa):
    """The picture of a tile with the day's numbers in it; the drawn picture when the numbers aren't ready yet."""
    if key == "hunt":
        got = d.hunt()
        if got and got.get("picks"):
            from p_scanner import short_name
            rows = ""
            for pk in got["picks"][:3]:
                lg = T.logo_obj(pk["sym"], 30)
                rows += (f'<div class="r"><span class="lg">{lg}</span><span class="nm"><b>{T.esc(T.sym_label(pk["sym"]))}</b>'
                         f'<span><em>{T.esc(short_name(pk["setup"]))}</em> · {T.esc(T.name_line(pk["sym"], pk["name"]))}</span></span>'
                         f'{_ring_html(pk["score"], pk["grade"])}</div>')
            more = max(0, got["opp"] - 3)
            tail = f'<div class="more">{T.esc(L(f"+{more} more opportunities today", f"+{more} فرص ثانية اليوم"))}</div>' if more else ""
            return f'<div class="vz picks">{rows}{tail}</div>', got
        return _vz(key, f), None
    if key == "bots":
        b = d.bots()
        if b and "bal" in b:
            together = L("The site's bots, together", "بوتات الموقع مع بعض")
            return (f'<div class="vz stat"><div class="l">{T.esc(together)}</div>'
                    f'<div class="big"><b>{T.esc(MK.money(b["bal"]))}</b>{T.pill(b["ret"])}</div>'
                    f'<div class="row"><span>{T.icon("emoji_events")} {T.esc(b["best"])}</span>{T.pill(b["best_ret"])}</div>'
                    f'<div class="row"><span>{T.esc(L("Open trades", "صفقات مفتوحة"))}</span><b>{b["open"]}</b></div></div>'), b
        return _vz(key, f), b
    if key == "news":
        st_ = d.stories()[:3]
        if st_:
            titles = [str(n.get("title", "")) for n in st_]
            if is_ar() and any(not re.search("[\u0600-\u06FF]", t) for t in titles):
                try:
                    titles = [t2 or t1 for t1, t2 in zip(titles, data.translate(titles, budget=3))]
                except Exception:
                    pass
            rows = ""
            for n, title in zip(st_, titles):
                sc = ""
                try:
                    sc = f'<span class="sc">{int(n["iq"]["score"])}/10</span>'
                except Exception:
                    pass
                when = T.time_ago(n["time"], is_ar()) if n.get("time") is not None else ""
                rows += (f'<div class="s"><div class="t" dir="auto">{T.esc(title)}</div>'
                         f'<div class="m">{sc}{T.icon("schedule")}{T.esc(str(n.get("source", "")))} · {T.esc(when)}</div></div>')
            return f'<div class="vz story">{rows}</div>', st_[0]
        return (f'<div class="vz story"><div class="t">{T.esc(L("The news bot is collecting the latest headlines from 35 feeds.", "بوت الأخبار يجمع آخر العناوين من 35 مصدراً."))}</div></div>'), None
    if key == "mood":
        v = d.fg()
        if v is not None:
            v = max(0.0, min(100.0, float(v)))
            nm = ""
            try:
                snap = d.snap()
                res = snap.get("res") or {}
                net = res.get("net") if isinstance(res, dict) else None
                if net is not None:
                    nm = (f'<div class="row"><span>{T.icon("newspaper")} {T.esc(L("News mood", "مزاج الأخبار"))}</span>'
                          f'<b>{T.esc(("+" if net > 0 else "") + f"{net:.0f}")}</b></div>')
            except Exception:
                pass
            return (f'<div class="vz fgm"><div class="top"><b>{v:.0f}<small style="font-size:12px;opacity:.7">/100</small></b><span>{T.esc(_fg_label(v))}</span></div>'
                    f'<div class="bar"><i style="inset-inline-start:{v:.0f}%"></i></div>'
                    f'<div class="zs"><span>{T.esc(L("Fear", "خوف"))}</span><span>{T.esc(L("Neutral", "محايد"))}</span><span>{T.esc(L("Greed", "طمع"))}</span></div>{nm}</div>'), v
        return (f'<div class="vz fgm"><div class="top"><b>—</b></div><div class="bar"></div></div>'), None
    if key == "cal":
        days = [L("Sun", "أحد"), L("Mon", "اثنين"), L("Tue", "ثلاثاء"), L("Wed", "أربعاء"), L("Thu", "خميس")] if sa else \
            [L("Mon", "اثنين"), L("Tue", "ثلاثاء"), L("Wed", "أربعاء"), L("Thu", "خميس"), L("Fri", "جمعة")]
        dots = [3, 1, 4, 2, 2]
        cells = "".join(f'<span><b>{T.esc(dn)}</b><i>{"●" * k}</i></span>' for dn, k in zip(days, dots))
        return f'<div class="vz days">{cells}</div>', None
    return _vz(key, f), None


# the tiles that are not in TOOLS: the news page and the mood page, the calendar
TILES = {
    "news": ("news", "newspaper", "news", ("Smart news", "أخبار ذكية"), ("Market news", "أخبار السوق"),
             ("Every headline read by the bot, scored out of 10, with why it matters to you.",
              "كل خبر يقراه البوت ويعطيه درجة من 10، ويقول لك ليش يهمك."), ("Read today's news", "اقرأ أخبار اليوم")),
    "mood": ("sentiment", "speed", "mood", ("Right now", "الحين"), ("Fear & Greed", "الخوف والطمع"),
             ("Is the market scared or greedy today? Seven signals in one number.",
              "السوق خايف ولا طمعان اليوم؟ سبع إشارات في رقم واحد."), ("What drives it", "وش يحرّكه")),
    "cal": ("earnings", "event_upcoming", "cal", ("This week", "هالأسبوع"), ("Calendars", "التقويم"),
            ("Earnings, economic events, dividends and IPOs, day by day.",
             "الأرباح والأحداث الاقتصادية والتوزيعات والاكتتابات، يوم بيوم."), ("Open the calendar", "افتح التقويم")),
}
TONE_CSS = """<style data-lm="keep">.ovad.news{--a1:#7C2D12;--a2:#B91C1C;--sh:rgba(185,28,28,.7)}.ovad.mood{--a1:#312E81;--a2:#0F766E;--sh:rgba(49,46,129,.75)}
.ovad.cal{--a1:#1F2937;--a2:#4338CA;--sh:rgba(67,56,202,.7)}</style>"""


# ---------------------------------------------------------------- the page's data, kept ready in the background (warm.py)
_HM_DEFAULT = {False: ("sp500", "1D", "cap"), True: ("sa_all", "1D", "cap")}      # the heat map's first choices


def _compute_lists(sa):
    """(the market's moves, its lists); None when the quotes couldn't be read (not kept: asked for again soon)."""
    if sa:
        mv = data.sa_moves()
        return (mv, PM.sa_lists(mv)) if not mv.empty else None
    mv = PM._universe_moves()
    lists = {k: PM._list(k, mv) for k in PM.LISTS}
    return (mv, lists) if not mv.empty or any(not df.empty for df, _ in lists.values()) else None


def _compute_heat(sa):
    ukey, period, sizing = _HM_DEFAULT[sa]
    syms = list(tasi.SYMBOLS) if sa else list(SP500)
    df, source = PM.heatmap_frame(ukey, period, sizing, syms=syms)
    if df is None or df.empty:
        return None                                  # not kept: tried again by the next visitor
    return {(ukey, period, sizing): (df, source)}


def _compute_stories(m, sa):
    items = PM.top_stories(3, market=m)
    tick = sorted({s_ for n in items for s_ in n["tickers"]})
    chg = (data.quick_changes(tick) if sa else data.changes(tick)) if tick else {}
    return {"items": items, "chg": chg}


def _compute_summary():
    px = PM._tile_prices(False)
    mv, lists = warm.get("lists:us", lambda: _compute_lists(False), 300) or (pd.DataFrame(), {})
    if not lists:
        return None
    return PM.summary_data(px, mv, lists)


def _jobs(sa):
    """Everything the page needs, with how long each stays fresh (seconds)."""
    m = MK.SA if sa else MK.US
    # in order of importance: the first pieces are made first (two at a time); the heavy ones last, never waited for
    jobs = {f"tiles:{m}": (lambda: PM._tile_prices(sa), 300),       # one per market: the background work runs outside any session
            f"snap:{m}": (lambda: PNI.compute_snapshot(m, 24), 600),
            f"stories:{m}": (lambda: _compute_stories(m, sa), 600),
            f"lists:{m}": (lambda: _compute_lists(sa), 600)}
    if not sa:
        jobs["macro"] = (data.macro, 3600)
        jobs["summary"] = (_compute_summary, 600)
    jobs.update({"xb": (lambda: __import__("xbots").load_all()[0], 300),
                 f"heat:{m}": (lambda: _compute_heat(sa), 600),
                 f"hunt:{m}": (lambda: _compute_hunt(sa), 600)})
    return jobs


LATER = ("heat", "hunt", "xb")                   # the page never waits for these: it shows them once they are ready


def _get(sa, key):
    m = MK.SA if sa else MK.US
    jobs = _jobs(sa)
    k = key if key in jobs else f"{key}:{m}"
    fn, ttl = jobs[k]
    return _timed(f"get {k}", warm.get, k, fn, ttl, 0 if key in LATER else 60)


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
        if "lists" not in self._got:
            v = _get(self.sa, "lists")
            if v is None:                            # not ready in the background (the quotes failed there): read here
                v = _compute_lists(self.sa)
            empty = (pd.DataFrame(), {k: pd.DataFrame() for k in PM.SA_LISTS}) if self.sa else \
                (pd.DataFrame(), {k: (pd.DataFrame(), True) for k in PM.LISTS})
            self._got["lists"] = v if v is not None else empty
        return self._got["lists"]

    def _st(self):
        v = self._one("stories", {})
        return v if isinstance(v, dict) else {"items": v or [], "chg": None}      # (kept by an older version: the list alone)

    def stories(self):
        return self._st().get("items") or []

    def story_chg(self):
        return self._st().get("chg")

    def summary(self):
        return None if self.sa else self._one("summary", None)

    def fg(self):
        return None                                  # the Fear & Greed dial left the home page (its own page has it)

    def hunt(self):
        return self._one("hunt", None)

    def xb(self):
        return self._one("xb", {})

    def bots(self):
        if "bots" not in self._got:
            self._got["bots"] = _bots_live(MK.SA if self.sa else MK.US)
        return self._got["bots"]

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
        ui.html(PM.stories_html(stories, d.lg(), sa=d.sa, chg=d.story_chg()))
    else:
        st.caption(L("No trending stories right now.", "لا توجد أخبار رائجة حالياً."))


def _in_news(d):
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


def _regime(d):
    """The market's mood strip (the hunter's reading: the index's trend, the share of stocks above their averages, highs and lows)."""
    got = d.hunt()
    reg = got.get("reg") if got else None
    if reg:
        import p_scanner as PS
        css = "<style>" + "\n".join(l for l in PS.CSS.splitlines() if ".hnreg" in l) + "</style>"   # the strip's own styles
        ui.sec("explore", "The market today", "السوق اليوم")
        ui.html(css + PS.mood_html(reg))


def _summary(d):
    ui.sec("summarize", "Market summary", "ملخص السوق")
    mv, lists = d.lists()
    with st.container(key="ovsum"):
        if d.sa:
            ui.html(PM.summary_html_sa(d.px, mv, lists, d.lg()))
        else:
            ui.html(PM.summary_html(d.summary() or PM.summary_data(d.px, mv, lists), d.lg()))


def _summary_and_mood(d):
    """The market summary on one side, the news mood and the Fear & Greed dial on the other."""
    a, b = st.columns([1.9, 1], gap="large")
    with a:
        ui.safe(_summary, d)
    with b:
        ui.safe(_mood, d.snap(), d.fg(), d.sa, d.xb())


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


def _mood(snap, v, sa=False, xb=None):
    ui.sec("speed", "The market's mood", "مزاج السوق")
    with st.container(key="ovmood"):
        if snap and snap["res"]:
            ui.html(PNI.dial_html(snap["res"], snap["hrs"]))
        else:
            st.caption(L("The news mood is not available right now.", "مزاج الأخبار غير متاح حالياً."))
        st.button(L("Read the news like an analyst", "اقرأ الأخبار مثل المحلل"), key="ovgo_ni", icon=":material/neurology:", width="stretch",
                  on_click=_open_tool, args=("ni", "newsintel"))
        # the X bots of this market in one card: what X's crowd feels, bot by bot
        import p_xbots as PX
        ui.html(PX.summary_html(MK.SA if sa else MK.US, xb))
        st.button(L("Meet the X bots", "تعرّف على بوتات X"), key="ovgo_xb", icon=":material/arrow_forward:", width="stretch",
                  on_click=_open_tool, args=("xbots", "xbots"))


def _markets(px, sa, macro=None):
    ui.sec("monitoring", "Markets at a glance", "الأسواق بلمحة")
    groups = PM.SA_TILES if sa else U.MARKET_TILES
    names = [L(gen, gar) for gen, gar in groups]
    if not sa:                                       # the economic indicators as the last tab of the strip
        names.append(L("Key economic indicators", "أهم المؤشرات الاقتصادية"))
    tabs = st.tabs(names)
    if not sa:
        with tabs[-1]:
            if macro is not None:
                _timed("indicators", ui.safe, PM.indicators_section, True, macro, False)
            else:
                st.caption(L("The economic indicators are on their way: they show in a moment.", "المؤشرات الاقتصادية في الطريق: تطلع بعد شوي."))
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


def _heat(d):
    pre = d.heat()
    if pre is None:                                  # being made in the background: a word now, the map on the next visit
        ui.sec("grid_view", "Stock heatmap", "خريطة الأسهم الحرارية")
        st.caption(L("The heat map is being drawn in the background: it shows in a minute.", "الخريطة الحرارية تنرسم بالخلفية: تطلع بعد دقيقة."))
        return
    PM.heatmap_section(pre)


def page_overview():
    sa = MK.is_sa()
    ui.html('<span class="css-anchor"></span>\n' + CSS + PNI.CSS + PNI.CSS2)
    ui.html('<span class="css-anchor"></span>\n' + home.CSS)
    t0 = time.time()
    warm.prefetch(_jobs(sa))                         # every piece the page needs, side by side, in the background
    import threading                                 # and the other market's, once, a little later, so a switch to it opens at once
    threading.Timer(240, warm.prefetch, args=(_jobs(not sa),), kwargs={"want": False}).start()
    px = _get(sa, "tiles") or {}
    PM.ticker_tape(px)
    ui.html(home.top_html(_chips(px, sa)))
    f = _timed("facts", _facts)
    d = _Day(px, sa)
    # the page as a magazine: the news across the page, then each part with tool cards (adverts) beside it - one on the
    # right, two on the left, the Robo Advisor as a banner across the page, two on the right, two on the left - and two
    # wide ones at the foot
    with st.container(key="ovpage"):
        ui.html(TONE_CSS)
        _timed("top", ui.safe, _top, d)
        _timed("part a", _with_ads, "a", "right", ["ai"], d, f, sa,
               lambda: (ui.safe(_in_news, d), ui.safe(_markets, px, sa, d.macro())))
        _timed("regime", ui.safe, _regime, d)
        _timed("summary", ui.safe, _summary_and_mood, d)
        _timed("part b", _with_ads, "b", "left", ["hunt", "bots"], d, f, sa, lambda: ui.safe(_movers, d))
        _timed("banner", ui.safe, _banner, "robo", d, f, sa)
        _timed("part c", _with_ads, "c", "right", ["pf", "earn"], d, f, sa, lambda: _timed("heatmap", ui.safe, _heat, d))
        last = [k for k in ("screener", "news", "academy", "xbots") if _available(k, sa)]
        if last:
            with st.container(key="ovfoot"):
                ui.sec("apps", "More tools to try", "أدوات ثانية تستاهل تجربها")
                for i in range(0, len(last), 2):
                    with st.container(key=f"ovads_z{i}"):
                        for k in last[i:i + 2]:
                            _card(k, d, f, sa, wide=True)
    if sa:
        st.caption(L("Prices from Yahoo Finance (may be delayed). The Saudi market trades Sunday to Thursday, 10 am to 3 pm Riyadh time.",
                     "الأسعار من Yahoo Finance (قد تكون متأخرة). السوق السعودي يتداول من الأحد للخميس، من 10 الصبح لين 3 العصر بتوقيت الرياض."))
    ui.foot()
    if _PROF:
        print(f"[prof] page {'sa' if sa else 'us'} total {time.time() - t0:.2f}s", flush=True)


BUILD = "23.4.56"
