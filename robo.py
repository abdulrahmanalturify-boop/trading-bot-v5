"""
robo.py - TURA Robo Advisor: a short questionnaire in the shape of an Investment Policy Statement (IPS), a portfolio of
low-cost ETFs built from the answers, and its management with virtual money.

The answers give two scores from 0 to 10: the ABILITY to take risk (time horizon, age, income, emergency fund, the share of
savings, withdrawals) and the WILLINGNESS (the goal, the reaction to a fall, experience, the loss that can be accepted, the
range picked). The risk level (1-10) follows the lower of the two, then the limits the answers set: a short horizon, a goal
of protecting capital or of income, and the largest loss accepted in a bad year (the highest level whose bad year, about 1
in 20, stays within it). Each level is a strategic mix of stocks (US, international, emerging), bonds, inflation-protected
bonds, cash, real estate and gold, held in conventional ETFs or in Sharia-compliant ones (Islamic stock funds and sukuk, no
interest-bearing bonds, cash kept as cash).

The portfolio is managed by replaying its policy over the real daily closes (adjusted for dividends, so dividends are
reinvested) from the day it was opened: the first investment at the first close after it, each month's deposit on the first
trading day of the month (into what is under its target first), a review each quarter (back to the targets) and a
rebalance as soon as a fund leaves its band. Nothing runs in the background: the same replay at every visit gives the same
history and today's value.

Kept in the paper bots' table like the paper portfolio: the row "<portfolio key>:robo" (the owner's key, or the visitor's
own code), so it follows the same code from device to device. Its key (the strategy column) starts with "__portfolio__", so
the Paper Bots page never lists it.
"""
import json
import math
import os
import tempfile
import threading
from datetime import timedelta

import numpy as np
import pandas as pd
import streamlit as st

import data
import mcal
import portfolio as PF
import robobot as RB

# ---------------------------------------------------------------- the questionnaire
SECTIONS = [("goals", "flag", "Goals", "الأهداف"),
            ("ability", "shield_person", "Ability", "القدرة على المخاطرة"),
            ("will", "psychology", "Willingness", "الرغبة في المخاطرة"),
            ("prefs", "tune", "Preferences", "التفضيلات"),
            ("fund", "savings", "Funding", "التمويل")]

# each option: (value, icon, label en, label ar, sub en, sub ar, score 0-4, extra)
QUESTIONS = [
    {"id": "goal", "sec": "goals", "score": "will", "icon": "flag",
     "en": "What is the main goal for this money?", "ar": "وش الهدف الرئيسي من هالمبلغ؟",
     "why_en": "The goal sets the return the portfolio aims for, and how much it may swing to get there.",
     "why_ar": "الهدف يحدد العائد اللي تستهدفه المحفظة، وكم تتحمل تذبذب عشان توصله.",
     "opts": [("keep", "shield", "Protect my capital", "أحافظ على رأس مالي", "Small, steady gains; avoid losses",
               "نمو بسيط وثابت وأتجنب الخسائر", 0, {"cap": 3}),
              ("income", "payments", "Regular income", "دخل منتظم", "Dividends and interest along the way",
               "توزيعات وعوائد على طول الطريق", 1.5, {"cap": 7, "income": True}),
              ("balanced", "balance", "Balanced growth", "نمو متوازن", "Growth with moderate ups and downs",
               "نمو مع صعود ونزول معتدل", 2.5, {}),
              ("growth", "trending_up", "Long-term growth", "نمو طويل المدى", "Build wealth; market swings are fine",
               "أبني ثروة وأتقبل تقلبات السوق", 3.5, {}),
              ("max", "rocket_launch", "Maximum growth", "أعلى نمو ممكن", "The highest return; big swings are fine",
               "أعلى عائد حتى لو التقلبات كبيرة", 4, {})]},
    {"id": "horizon", "sec": "goals", "score": "ability", "icon": "hourglass_top",
     "en": "When will you need most of this money?", "ar": "متى بتحتاج أغلب هالمبلغ؟",
     "why_en": "Time is the strongest cushion: the longer the money stays, the more time a fall has to recover.",
     "why_ar": "الوقت أقوى حماية: كل ما طالت مدة الاستثمار، صار عند أي نزول وقت يتعافى فيه.",
     "opts": [("lt3", "hourglass_bottom", "Within 3 years", "خلال 3 سنوات", "A near-term need", "احتياج قريب", 0, {"cap": 3, "years": 3}),
              ("3to5", "schedule", "3 to 5 years", "من 3 إلى 5 سنوات", "Medium term", "مدى متوسط", 1, {"cap": 5, "years": 5}),
              ("5to10", "event", "5 to 10 years", "من 5 إلى 10 سنوات", "Room to ride out a cycle", "وقت كافي لدورة سوق كاملة",
               2.5, {"years": 10}),
              ("10to20", "date_range", "10 to 20 years", "من 10 إلى 20 سنة", "Long term", "مدى طويل", 3.5, {"years": 15}),
              ("gt20", "all_inclusive", "More than 20 years", "أكثر من 20 سنة", "Retirement or the next generation",
               "للتقاعد أو للجيل الجاي", 4, {"years": 25})]},
    {"id": "age", "sec": "ability", "score": "ability", "icon": "cake",
     "en": "How old are you?", "ar": "كم عمرك؟",
     "why_en": "Younger investors have more working years ahead to add money and wait out a fall.",
     "why_ar": "كل ما كنت أصغر، صار قدامك سنين عمل أكثر تضيف فيها وتصبر على أي نزول.",
     "opts": [("u30", "bolt", "Under 30", "أقل من 30", "", "", 4, {}),
              ("30s", "work", "30 – 44", "30 – 44", "", "", 3, {}),
              ("45s", "family_restroom", "45 – 54", "45 – 54", "", "", 2, {}),
              ("55s", "chair", "55 – 64", "55 – 64", "", "", 1, {}),
              ("65p", "elderly", "65 or older", "65 وأكثر", "", "", 0, {})]},
    {"id": "income", "sec": "ability", "score": "ability", "icon": "work",
     "en": "How stable is your income?", "ar": "كيف استقرار دخلك؟",
     "why_en": "A steady income means you never have to sell investments at a bad moment to pay the bills.",
     "why_ar": "الدخل الثابت يعني إنك ما تضطر تبيع استثماراتك في وقت سيئ عشان تغطي مصاريفك.",
     "opts": [("very", "verified", "Very stable", "مستقر جداً", "A secure job or a steady pension", "وظيفة ثابتة أو راتب تقاعدي", 4, {}),
              ("stable", "trending_flat", "Stable", "مستقر", "Unlikely to change much", "غالباً ما يتغير كثير", 3, {}),
              ("varies", "show_chart", "It varies", "متغير", "Commission, freelance or business income", "عمولات أو عمل حر أو تجارة", 1.5, {}),
              ("none", "help", "Uncertain or none", "غير مضمون أو ما فيه دخل", "No regular income right now", "ما فيه دخل منتظم حالياً",
               0, {})]},
    {"id": "emergency", "sec": "ability", "score": "ability", "icon": "savings",
     "en": "Do you have an emergency fund besides this money?", "ar": "عندك مبلغ للطوارئ غير هالمبلغ؟",
     "why_en": "Cash for 3 to 6 months of expenses means a market fall never forces you to sell.",
     "why_ar": "وجود كاش يكفي مصاريف 3 إلى 6 شهور يعني إن نزول السوق ما يجبرك تبيع.",
     "opts": [("6p", "savings", "6 months or more", "6 شهور أو أكثر", "Of my expenses, in cash", "من مصاريفي، كاش", 4, {}),
              ("3to6", "account_balance", "3 to 6 months", "من 3 إلى 6 شهور", "A solid cushion", "احتياطي جيد", 3, {}),
              ("lt3", "hourglass_empty", "Less than 3 months", "أقل من 3 شهور", "A thin cushion", "احتياطي بسيط", 1.5, {}),
              ("none", "money_off", "None", "ما عندي", "This money is my safety net too", "هالمبلغ هو احتياطي الطوارئ بعد", 0, {})]},
    {"id": "share", "sec": "ability", "score": "ability", "icon": "pie_chart",
     "en": "What share of your savings is this money?", "ar": "هالمبلغ كم يمثل من مدخراتك؟",
     "why_en": "The more of your wealth is at stake, the more a fall would hurt your life, not just the account.",
     "why_ar": "كل ما زادت نسبة المبلغ من ثروتك، صار أي نزول يأثر على حياتك مو بس على الحساب.",
     "opts": [("lt25", "donut_small", "Less than a quarter", "أقل من الربع", "", "", 4, {}),
              ("25to50", "donut_large", "A quarter to a half", "من الربع إلى النص", "", "", 3, {}),
              ("50to75", "pie_chart", "A half to three quarters", "من النص إلى ثلاثة أرباع", "", "", 1.5, {}),
              ("gt75", "circle", "Almost all of it", "تقريباً كلها", "", "", 0, {})]},
    {"id": "withdraw", "sec": "ability", "score": "ability", "icon": "output",
     "en": "Will you need to take money out along the way?", "ar": "بتحتاج تسحب من المبلغ على الطريق؟",
     "why_en": "Money you will need soon is kept in cash or near-cash, so it is there when you need it.",
     "why_ar": "المبلغ اللي بتحتاجه قريب ينحفظ كاش أو شبه كاش، عشان يكون جاهز وقت ما تحتاجه.",
     "opts": [("no", "lock", "No, it stays invested", "لا، يبقى مستثمر", "", "", 4, {"cash": 0}),
              ("some", "event_repeat", "A little each year", "شوي كل سنة", "Up to about 5% a year", "تقريباً لين 5% بالسنة", 2.5, {"cash": 5}),
              ("big", "shopping_bag", "A large part within 2 years", "جزء كبير خلال سنتين", "A home, a wedding, studies...",
               "بيت، زواج، دراسة...", 0, {"cash": 20})]},
    {"id": "risk", "sec": "will", "score": "will", "icon": "speed",
     "en": "How would you describe your risk tolerance?", "ar": "كيف توصف تحمّلك للمخاطر؟",
     "why_en": "Five grades from conservative to aggressive. The plan never goes beyond the grade you pick, and stays lower if your "
               "other answers call for it.",
     "why_ar": "خمس درجات من المتحفظ إلى الجريء. الخطة ما تتعدى الدرجة اللي تختارها، وتنزل عنها إذا إجاباتك الثانية تتطلب كذا.",
     "opts": [("conservative", "shield", "Conservative", "متحفظ", "Protect what I have; small, steady gains",
               "أحمي اللي عندي، ونمو بسيط وثابت", 0, {"cap": 2, "lv": 2}),
              ("modcons", "security", "Moderately conservative", "متحفظ معتدل", "Mostly stability, a little growth",
               "استقرار أكثر مع شوية نمو", 1, {"cap": 4, "lv": 4}),
              ("moderate", "balance", "Moderate", "معتدل", "A balance of growth and stability", "توازن بين النمو والاستقرار", 2,
               {"cap": 6, "lv": 6}),
              ("modagg", "trending_up", "Moderately aggressive", "جريء معتدل", "Growth first; clear swings are fine",
               "النمو أولاً، وأتقبل تقلبات واضحة", 3, {"cap": 8, "lv": 8}),
              ("aggressive", "rocket_launch", "Aggressive", "جريء", "The most growth; big swings are fine",
               "أعلى نمو حتى مع تقلبات كبيرة", 4, {"cap": 10, "lv": 10})]},
    {"id": "drop", "sec": "will", "score": "will", "icon": "trending_down",
     "en": "Your portfolio falls 20% in a few months. What do you do?", "ar": "محفظتك نزلت 20% خلال كم شهر. وش تسوي؟",
     "why_en": "Markets have done this many times (2008, 2020, 2022). What you would really do matters more than any number.",
     "why_ar": "السوق سواها مرات كثيرة (2008 و2020 و2022). ردة فعلك الحقيقية أهم من أي رقم.",
     "opts": [("sellall", "logout", "Sell everything", "أبيع كل شي", "Stop the losses now", "أوقف الخسارة فوراً", 0, {}),
              ("sellsome", "remove_circle", "Sell some", "أبيع جزء", "Lower the risk", "أخفف المخاطرة", 1.5, {}),
              ("hold", "pause_circle", "Hold and wait", "أصبر وأنتظر", "Stick to the plan", "ألتزم بالخطة", 3, {}),
              ("buy", "add_circle", "Buy more", "أشتري زيادة", "Prices are on sale", "الأسعار صارت أرخص", 4, {})]},
    {"id": "exp", "sec": "will", "score": "will", "icon": "school",
     "en": "How much investing experience do you have?", "ar": "وش خبرتك في الاستثمار؟",
     "why_en": "Knowing how markets behave makes the ups and downs easier to live with.",
     "why_ar": "فهمك لطبيعة الأسواق يخلي الصعود والنزول أسهل في التعامل.",
     "opts": [("none", "emoji_people", "None yet", "ما عندي خبرة", "This is my first time", "هذي أول مرة", 1, {}),
              ("some", "menu_book", "Some", "بسيطة", "Savings, deposits or funds", "ادخار أو ودائع أو صناديق", 2, {}),
              ("good", "query_stats", "Good", "جيدة", "I have owned stocks or ETFs", "سبق امتلكت أسهم أو صناديق مؤشرات", 3, {}),
              ("pro", "insights", "Advanced", "متقدمة", "I follow markets closely", "أتابع الأسواق عن قرب", 4, {})]},
    {"id": "maxloss", "sec": "will", "score": "will", "icon": "south",
     "en": "The most you could accept losing in a bad year?", "ar": "أقصى خسارة تتقبلها في سنة سيئة؟",
     "why_en": "Every portfolio has bad years. This sets how deep yours may go before it stops fitting you.",
     "why_ar": "كل محفظة تمر بسنين سيئة. هذا يحدد لأي عمق ممكن تنزل محفظتك وتبقى مناسبة لك.",
     "opts": [("5", "", "5%", "5%", "Very little", "بسيطة جداً", 0, {"loss": 5}),
              ("10", "", "10%", "10%", "Small", "بسيطة", 1.5, {"loss": 10}),
              ("20", "", "20%", "20%", "Moderate", "متوسطة", 2.5, {"loss": 20}),
              ("30", "", "30%", "30%", "Large", "كبيرة", 3.5, {"loss": 30}),
              ("40", "", "40% or more", "40% أو أكثر", "Whatever it takes", "مهما كانت", 4, {"loss": 99})]},
    {"id": "range", "sec": "will", "score": "will", "icon": "candlestick_chart",
     "en": "Which one-year range would you pick?", "ar": "أي مدى لسنة وحدة تختار؟",
     "why_en": "Higher returns come with deeper falls. Each pair is a bad year and a good year of the same portfolio.",
     "why_ar": "العائد الأعلى يجي معه نزول أعمق. كل خيار هو سنة سيئة وسنة جيدة لنفس المحفظة.",
     "opts": [("a", "", "A", "أ", "", "", 0.5, {"lo": -3, "hi": 8}),
              ("b", "", "B", "ب", "", "", 1.75, {"lo": -10, "hi": 16}),
              ("c", "", "C", "ج", "", "", 3, {"lo": -20, "hi": 28}),
              ("d", "", "D", "د", "", "", 4, {"lo": -30, "hi": 40})]},
    {"id": "sharia", "sec": "prefs", "score": None, "icon": "mosque",
     "en": "Do you want a Sharia-compliant portfolio?", "ar": "تبي المحفظة متوافقة مع الشريعة؟",
     "why_en": "Sharia-compliant funds screen out interest-based businesses and replace bonds with sukuk.",
     "why_ar": "الصناديق المتوافقة تستبعد الشركات القائمة على الفوائد، وتستبدل السندات بالصكوك.",
     "opts": [("yes", "mosque", "Yes, Sharia-compliant", "نعم، متوافقة مع الشريعة", "Islamic ETFs and sukuk; no interest-bearing bonds",
               "صناديق إسلامية وصكوك، بدون سندات ربوية", None, {"sharia": True}),
              ("no", "public", "No preference", "ما يفرق", "The broadest, lowest-cost index funds", "أوسع صناديق المؤشرات وأقلها تكلفة",
               None, {"sharia": False})]},
]
QIDS = [q["id"] for q in QUESTIONS]
STEPS = QIDS + ["fund"]                 # the last screen: the amount and the monthly deposit
Q = {q["id"]: q for q in QUESTIONS}


def opt(qid, value):
    """The option tuple chosen for a question (None when not answered or unknown)."""
    for o in Q[qid]["opts"]:
        if o[0] == value:
            return o
    return None


# ---------------------------------------------------------------- the funds
# sleeve -> (conventional ETF, Sharia-compliant ETF)
SLEEVES = ["us", "div", "intl", "em", "bond", "tips", "cash", "reit", "gold", "bot"]
ETF = {"us": ("VTI", "SPUS"), "div": ("SCHD", "SPUS"), "intl": ("VEA", "UMMA"), "em": ("VWO", "UMMA"), "bond": ("BND", "SPSK"),
       "tips": ("VTIP", "SPSK"), "cash": ("SGOV", "CASH"), "reit": ("VNQ", "SPRE"), "gold": ("GLD", "GLD"), "bot": ("BOT", "BOT")}
BOT = "BOT"                             # the Opportunity Bot's slice (robobot.py): not a fund, a book of its own
# ticker -> (name, class en, class ar, colour, group: stocks / bonds / cash / real / gold)
FUNDS = {
    "VTI": ("Vanguard Total Stock Market ETF", "US stocks", "أسهم أمريكية", "#3B8BEB", "stocks"),
    "SCHD": ("Schwab U.S. Dividend Equity ETF", "US dividend stocks", "أسهم توزيعات أمريكية", "#60A5FA", "stocks"),
    "VEA": ("Vanguard FTSE Developed Markets ETF", "Developed-market stocks", "أسهم الدول المتقدمة", "#2DB6EB", "stocks"),
    "VWO": ("Vanguard FTSE Emerging Markets ETF", "Emerging-market stocks", "أسهم الأسواق الناشئة", "#7B45F0", "stocks"),
    "BND": ("Vanguard Total Bond Market ETF", "US bonds", "سندات أمريكية", "#34D399", "bonds"),
    "VTIP": ("Vanguard Short-Term Inflation-Protected Securities ETF", "Inflation-protected bonds", "سندات محمية من التضخم",
             "#2DD4BF", "bonds"),
    "SGOV": ("iShares 0-3 Month Treasury Bond ETF", "Treasury bills (cash)", "أذونات خزينة (شبه نقد)", "#9D97A5", "cash"),
    "VNQ": ("Vanguard Real Estate ETF", "Real estate (REITs)", "عقارات (صناديق ريت)", "#F97316", "real"),
    "GLD": ("SPDR Gold Shares", "Gold", "ذهب", "#F5B94A", "gold"),
    "SPUS": ("SP Funds S&P 500 Sharia Industry Exclusions ETF", "US stocks (Sharia)", "أسهم أمريكية متوافقة", "#3B8BEB", "stocks"),
    "UMMA": ("Wahed Dow Jones Islamic World ETF", "World stocks ex-US (Sharia)", "أسهم عالمية متوافقة", "#2DB6EB", "stocks"),
    "SPSK": ("SP Funds Dow Jones Global Sukuk ETF", "Sukuk", "صكوك", "#34D399", "bonds"),
    "SPRE": ("SP Funds S&P Global REIT Sharia ETF", "Real estate (Sharia)", "عقارات متوافقة", "#F97316", "real"),
    "CASH": ("Cash", "Cash", "نقد", "#9D97A5", "cash"),
    "BOT": ("TURA Opportunity Bot", "Emerging companies & explosive moves", "الشركات الناشئة والانفجارات السعرية", "#EC4899", "bot"),
}
GROUPS = {"stocks": ("Stocks", "أسهم", "#3B8BEB"), "bonds": ("Bonds & sukuk", "سندات وصكوك", "#34D399"),
          "cash": ("Cash", "نقد", "#9D97A5"), "real": ("Real estate", "عقارات", "#F97316"), "gold": ("Gold", "ذهب", "#F5B94A"),
          "bot": ("Opportunity bot", "بوت الفرص", "#EC4899")}
BENCH = ("VT", "BND")                   # the policy benchmark: global stocks and US bonds, at the plan's own stock share

# the strategic mix of each level: stocks, bonds, inflation-protected bonds, cash, real estate, gold (percent)
CORE = {1: (10, 45, 15, 25, 0, 5), 2: (20, 45, 12, 15, 3, 5), 3: (30, 42, 10, 8, 5, 5), 4: (40, 38, 7, 5, 5, 5),
        5: (50, 32, 5, 3, 5, 5), 6: (60, 26, 4, 0, 5, 5), 7: (70, 19, 1, 0, 5, 5), 8: (80, 12, 0, 0, 4, 4),
        9: (88, 6, 0, 0, 3, 3), 10: (95, 0, 0, 0, 3, 2)}
# the five grades of risk tolerance, conservative to aggressive: two levels each (1-2, 3-4, 5-6, 7-8, 9-10)
TIERS = [("conservative", "Conservative", "متحفظ"), ("modcons", "Moderately conservative", "متحفظ معتدل"), ("moderate", "Moderate", "معتدل"),
         ("modagg", "Moderately aggressive", "جريء معتدل"), ("aggressive", "Aggressive", "جريء")]
PROFILES = {lv: TIERS[(lv - 1) // 2][1:] for lv in range(1, 11)}


def tier(level):
    """0..4: the grade of a risk level."""
    return (int(min(10, max(1, level))) - 1) // 2

# long-run assumptions per sleeve: expected return a year, volatility (percent) - for the projection, not a promise
ASSUME = {"us": (7.0, 16.0), "div": (6.8, 14.0), "intl": (6.5, 17.0), "em": (7.5, 22.0), "bond": (4.2, 6.0), "tips": (3.8, 3.0),
          "cash": (3.5, 0.5), "reit": (6.5, 20.0), "gold": (4.5, 15.0), "bot": (9.0, 35.0)}
ASSUME_SHARIA = {"bond": (4.5, 5.5), "tips": (4.5, 5.5), "cash": (0.0, 0.0)}
CORR = np.array([
    # us   div  intl  em   bond tips cash reit gold bot
    [1.00, .90, .85, .75, .10, .20, .00, .75, .05, .70],   # us
    [.90, 1.00, .80, .70, .15, .20, .00, .75, .05, .55],   # div
    [.85, .80, 1.00, .85, .10, .20, .00, .65, .15, .55],   # intl
    [.75, .70, .85, 1.00, .10, .25, .00, .60, .20, .55],   # em
    [.10, .15, .10, .10, 1.00, .70, .10, .25, .30, .00],   # bond
    [.20, .20, .20, .25, .70, 1.00, .10, .30, .40, .05],   # tips
    [.00, .00, .00, .00, .10, .10, 1.00, .00, .00, .00],   # cash
    [.75, .75, .65, .60, .25, .30, .00, 1.00, .10, .45],   # reit
    [.05, .05, .15, .20, .30, .40, .00, .10, 1.00, .05],   # gold
    [.70, .55, .55, .55, .00, .05, .00, .45, .05, 1.00],   # bot (long and short: less tied to the market than its stocks)
])
Z_BAD = 1.645                           # a bad year: about 1 year in 20


def _round_weights(w, step=0.5):
    """Weights rounded to `step` points that still add up to 100 (the rounding left over goes to the largest)."""
    w = {k: v for k, v in w.items() if v > 1e-9}
    if not w:
        return {}
    tot = sum(w.values())
    r = {k: round(v / tot * 100 / step) * step for k, v in w.items()}
    r = {k: v for k, v in r.items() if v > 0}
    big = max(r, key=r.get)
    r[big] = round(r[big] + 100 - sum(r.values()), 4)
    return r


def sleeves(level, income=False, cash=0, sharia=False):
    """{sleeve: weight %} of a risk level: its strategic mix, the stock part split US / developed / emerging (more emerging from
    level 8), half of the US part in dividend stocks for an income goal, and `cash` points set aside for withdrawals."""
    level = int(min(10, max(1, level)))
    eq, bd, tp, ca, re, go = CORE[level]
    us_, intl_, em_ = (.60, .25, .15) if level >= 8 else (.60, .28, .12)
    w = {"us": eq * us_, "intl": eq * intl_, "em": eq * em_, "bond": bd, "tips": tp, "cash": ca, "reit": re, "gold": go}
    if income:
        w["div"] = w["us"] / 2
        w["us"] -= w["div"]
    if cash:
        k = (100 - cash) / 100
        w = {s: v * k for s, v in w.items()}
        w["cash"] = w.get("cash", 0) + cash
    sat = RB.SAT.get(level, 0)                         # levels 9 and 10: a slice for the Opportunity Bot
    if sat:
        k = (100 - sat) / 100
        w = {s: v * k for s, v in w.items()}
        w["bot"] = sat
    return {s: v for s, v in w.items() if v > 1e-9}


def targets(sl, sharia=False):
    """{ticker: weight %} of a set of sleeves (two sleeves held in the same fund add up), rounded to half points."""
    out = {}
    for s, v in sl.items():
        t = ETF[s][1 if sharia else 0]
        out[t] = out.get(t, 0) + v
    return _round_weights(out)


def expected(sl, sharia=False):
    """(expected return a year %, volatility %, a bad year % (1 in 20)) of a set of sleeves, from the long-run assumptions."""
    w = np.array([sl.get(s, 0) / 100 for s in SLEEVES])
    tot = w.sum()
    if tot <= 0:
        return 0.0, 0.0, 0.0
    w = w / tot
    a = {**ASSUME, **(ASSUME_SHARIA if sharia else {})}
    mu = np.array([a[s][0] for s in SLEEVES])
    sd = np.array([a[s][1] for s in SLEEVES])
    cov = np.outer(sd, sd) * CORR
    m = float(w @ mu)
    v = float(math.sqrt(max(w @ cov @ w, 0)))
    return round(m, 2), round(v, 2), round(m - Z_BAD * v, 2)


# a 2008-style crisis, peak to trough (Oct 2007 - Mar 2009, rough): what each sleeve did
CRISIS = {"us": -51, "div": -50, "intl": -57, "em": -61, "bond": 6, "tips": -2, "cash": 2, "reit": -68, "gold": 20, "bot": -65}
CRISIS_SHARIA = {"bond": -6, "tips": -6, "cash": 0}


# three real storms, peak to trough (rough): what each kind of asset did - (en, ar, when en, when ar, {sleeve: %}, Sharia overrides)
SCENARIOS = {
    "gfc": ("2008 financial crisis", "الأزمة المالية 2008", "Oct 2007 – Mar 2009", "أكتوبر 2007 – مارس 2009", CRISIS, CRISIS_SHARIA),
    "covid": ("2020 COVID crash", "انهيار كورونا 2020", "Feb – Mar 2020", "فبراير – مارس 2020",
              {"us": -35, "div": -38, "intl": -34, "em": -33, "bond": -3, "tips": -5, "cash": 0.3, "reit": -43, "gold": -4, "bot": -45},
              {"bond": -5, "tips": -5, "cash": 0}),
    "rates": ("2022 rate shock", "صدمة الفائدة 2022", "Jan – Oct 2022", "يناير – أكتوبر 2022",
              {"us": -25, "div": -15, "intl": -28, "em": -30, "bond": -16, "tips": -5, "cash": 1, "reit": -33, "gold": -9, "bot": -65},
              {"bond": -10, "tips": -10, "cash": 0}),
}


def scenario(sl, key, sharia=False):
    """The plan's rough fall in one of the three storms (%)."""
    _, _, _, _, base, sh = SCENARIOS[key]
    c = {**base, **(sh if sharia else {})}
    tot = sum(sl.values()) or 1.0
    return round(sum(v / tot * c.get(s, 0) for s, v in sl.items()), 1)


def frontier(income=False, cash=0, sharia=False):
    """[(level, expected return, volatility, stock share)] of the ten levels for these answers."""
    out = []
    for lv in range(1, 11):
        sl = sleeves(lv, income, cash, sharia)
        mu, vol, _ = expected(sl, sharia)
        out.append((lv, mu, vol, stock_share(sl)))
    return out


def monthly_returns(curve):
    """{(year, month): return %} from a replay's time-weighted curve (the first month from its first day)."""
    if curve is None or len(curve) < 2:
        return {}
    tw = curve["twr"].astype(float)
    ends = tw.groupby([tw.index.year, tw.index.month]).last()
    out, prev = {}, float(tw.iloc[0])
    for (y, m), v in ends.items():
        out[(int(y), int(m))] = (float(v) / prev - 1) * 100
        prev = float(v)
    return out


def stress(sl, sharia=False):
    """The plan's rough fall in a 2008-style crisis (%), from what each kind of asset did then."""
    c = {**CRISIS, **(CRISIS_SHARIA if sharia else {})}
    tot = sum(sl.values()) or 1.0
    return round(sum(v / tot * c[s] for s, v in sl.items()), 1)


def stock_share(sl):
    return sum(v for s, v in sl.items() if s in ("us", "div", "intl", "em", "bot"))


def band(w):
    """The rebalancing band of a target weight (points either side)."""
    return 5.0 if w >= 20 else 3.0 if w >= 8 else 2.0


# ---------------------------------------------------------------- answers -> profile -> plan
def score(ans, kind):
    vals = [o[6] for q in QUESTIONS if q["score"] == kind for o in [opt(q["id"], ans.get(q["id"]))] if o is not None]
    return round(sum(vals) / len(vals) / 4 * 10, 2) if vals else None


def to_level(s):
    return int(min(10, max(1, 1 + round(s * 0.9))))


def extras(ans):
    """What the answers add besides the scores: income tilt, cash for withdrawals, Sharia, the horizon in years."""
    ex = {"income": False, "cash": 0, "sharia": False, "years": 10}
    for qid in ("goal", "horizon", "withdraw", "sharia"):
        o = opt(qid, ans.get(qid))
        if o:
            for k in ("income", "cash", "sharia", "years"):
                if k in o[7]:
                    ex[k] = o[7][k]
    return ex


def profile(ans, level=None):
    """Everything the plan needs from the answers. level: a level picked by hand (else the recommended one)."""
    ab, wl = score(ans, "ability"), score(ans, "will")
    ab = 5.0 if ab is None else ab
    wl = 5.0 if wl is None else wl
    ex = extras(ans)
    raw = to_level(min(ab, wl))
    caps = []
    o = opt("horizon", ans.get("horizon"))
    if o and "cap" in o[7]:
        caps.append(("horizon", o[7]["cap"]))
    o = opt("goal", ans.get("goal"))
    if o and "cap" in o[7]:
        caps.append(("goal", o[7]["cap"]))
    o = opt("risk", ans.get("risk"))
    if o:
        caps.append(("tolerance", o[7]["cap"]))
    o = opt("maxloss", ans.get("maxloss"))
    if o:
        loss = o[7]["loss"]
        fit = [lv for lv in range(1, 11) if -expected(sleeves(lv, ex["income"], ex["cash"], ex["sharia"]), ex["sharia"])[2] <= loss]
        caps.append(("loss", max(fit) if fit else 1))
    rec = raw
    for _, c in caps:
        rec = min(rec, c)
    binding = [k for k, c in caps if c == rec and c < raw]
    lv = rec if level is None else int(min(10, max(1, level)))
    sl = sleeves(lv, ex["income"], ex["cash"], ex["sharia"])
    mu, vol, bad = expected(sl, ex["sharia"])
    return {"crisis": stress(sl, ex["sharia"]), "stated": ans.get("risk"), "ability": ab, "will": wl, "raw": raw, "rec": rec, "level": lv, "caps": caps, "binding": binding,
            "governs": "ability" if ab < wl else "will" if wl < ab else "both", **ex,
            "sleeves": sl, "targets": targets(sl, ex["sharia"]), "mu": mu, "vol": vol, "bad": bad, "stocks": round(stock_share(sl), 1)}


def partial_level(ans):
    """The level the answers given so far point to (for the live meter in the questionnaire), None before any."""
    ab, wl = score(ans, "ability"), score(ans, "will")
    got = [s for s in (ab, wl) if s is not None]
    if not got:
        return None
    lv = to_level(min(got))
    for qid in ("horizon", "goal", "risk"):           # the limits the answers set (a short horizon, the goal, the grade picked)
        o = opt(qid, ans.get(qid))
        if o and "cap" in o[7]:
            lv = min(lv, o[7]["cap"])
    return lv


# ---------------------------------------------------------------- projection (Monte Carlo)
def project(mu, vol, amount, monthly, years, n=1500, seed=7, goal=None):
    """Months 0..years*12 with the 10th / 50th / 90th percentile of the value and the money put in, from `n` random paths of
    monthly returns (log-normal, the plan's expected return and volatility), deposits at the start of each month."""
    months = int(max(1, years) * 12)
    rng = np.random.default_rng(seed)
    m = math.log(1 + mu / 100) - (vol / 100) ** 2 / 2
    r = rng.normal(m / 12, (vol / 100) / math.sqrt(12), size=(n, months))
    g = np.exp(r)
    v = np.empty((n, months + 1))
    v[:, 0] = amount
    for t in range(months):
        v[:, t + 1] = (v[:, t] + (monthly if t > 0 else 0)) * g[:, t]
    inv = amount + monthly * np.maximum(np.arange(months + 1) - 1, 0)
    p10, p50, p90 = np.percentile(v, [10, 50, 90], axis=0)
    out = pd.DataFrame({"p10": p10, "p50": p50, "p90": p90, "invested": inv}, index=np.arange(months + 1))
    out.attrs["beat"] = float((v[:, -1] > inv[-1]).mean() * 100)
    if goal:
        out.attrs["goal_p"] = float((v[:, -1] >= goal).mean() * 100)
    return out


# ---------------------------------------------------------------- prices
def prices(tickers, period="5y"):
    """Daily closes adjusted for dividends and splits (columns: tickers; CASH is 1.0), dates without time, a day one fund
    did not trade carried from the day before."""
    real = sorted({t for t in tickers if t and t != "CASH"})
    got = data.history_many(real, period) if real else {}
    cols = {}
    for t in real:
        df = got.get(t)
        if df is None or getattr(df, "empty", True) or "Close" not in df:
            continue
        s = pd.to_numeric(df["Close"], errors="coerce").dropna()
        idx = pd.to_datetime(s.index)
        if getattr(idx, "tz", None) is not None:
            idx = idx.tz_convert(PF.ET).tz_localize(None)
        s.index = idx.normalize()
        cols[t] = s[~s.index.duplicated(keep="last")]
    px = pd.DataFrame(cols).sort_index()
    if len(px):
        px = px.ffill()
    if "CASH" in tickers:
        px["CASH"] = 1.0
    return px


# ---------------------------------------------------------------- the managed portfolio
def new_robo(ans, prof, amount, monthly, now=None):
    at = PF.iso(now or PF.utcnow())
    return {"v": 1, "created": at, "answers": dict(ans), "amount": float(amount),
            "plans": [{"at": at, "level": prof["level"], "rec": prof["rec"], "targets": prof["targets"], "sharia": prof["sharia"],
                       "stocks": prof["stocks"], "why": "start"}],
            "monthly": [{"at": at, "amount": float(monthly)}], "flows": [], "rev": 0}


def clean(state):
    if not isinstance(state, dict) or not state.get("plans") or not state.get("created"):
        return None
    state.setdefault("monthly", [])
    state.setdefault("flows", [])
    return state


def exec_day(at):
    """The trading day an instruction given at `at` is carried out (at that day's close)."""
    return pd.Timestamp(PF.order_session(at))


def settled_day(now=None):
    """The last trading day whose close has passed."""
    now = (now or PF.utcnow()).astimezone(PF.ET)
    d = now.date()
    s = PF.session(d)
    if s and now >= s[1]:
        return pd.Timestamp(d)
    return pd.Timestamp(mcal.prev_trading_day(d))


def _buy_toward(h, w, cash):
    """Dollar buys that put `cash` to work: what is under its target first, the rest by the targets."""
    tot = sum(h.values()) + cash
    deficit = {t: max(0.0, w[t] / 100 * tot - h.get(t, 0.0)) for t in w}
    s = sum(deficit.values())
    k = min(1.0, cash / s) if s > 0 else 0.0
    buy = {t: deficit[t] * k for t in w}
    rest = cash - sum(buy.values())
    if rest > 1e-9:
        for t in w:
            buy[t] += rest * w[t] / 100
    return buy


def _sell_toward(h, w, cash):
    """Dollar sales that raise `cash`: what is over its target first, the rest pro rata."""
    tot = sum(h.values())
    cash = min(cash, tot)
    left = tot - cash
    excess = {t: max(0.0, v - w.get(t, 0) / 100 * left) for t, v in h.items()}
    s = sum(excess.values())
    k = min(1.0, cash / s) if s > 0 else 0.0
    sell = {t: excess[t] * k for t in h}
    rest = cash - sum(sell.values())
    remain = {t: h[t] - sell[t] for t in h}
    rs = sum(remain.values())
    if rest > 1e-9 and rs > 0:
        for t in h:
            sell[t] += rest * remain[t] / rs
    return {t: -v for t, v in sell.items()}


def replay(robo, px, now=None, bench=False, bot=None):
    """The portfolio day by day from its first close to the last settled one, then valued at the latest prices.
    bench=True replays the policy benchmark (global stocks / US bonds at each plan's stock share) with the same money.
    bot: the Opportunity Bot's hunting list ({ticker: robobot.features}) for plans with a BOT slice (without it the slice
    waits in cash). Returns {curve: DataFrame[value, invested, flow, twr], units, cost, events, pending, start, last, live,
    book (the bot's robobot.Book or None)}."""
    now = now or PF.utcnow()
    plans = sorted(robo["plans"], key=lambda p: p["at"])
    if bench:
        plans = [{**p, "targets": {BENCH[0]: p["stocks"], BENCH[1]: 100 - p["stocks"]} if p["stocks"] < 100 else {BENCH[0]: 100}}
                 for p in plans]
    start = exec_day(robo["created"])
    last = settled_day(now)
    pdays = [(exec_day(p["at"]), p) for p in plans]
    mdays = sorted(((exec_day(m["at"]), m["amount"]) for m in robo.get("monthly") or []), key=lambda x: x[0])
    fdays = sorted(((exec_day(f["at"]), float(f["amount"]), f.get("note", "")) for f in robo.get("flows") or []), key=lambda x: x[0])
    tick = sorted({t for p in plans for t in p["targets"]})
    etfs = [t for t in tick if t != BOT]
    out = {"start": start, "last": last, "pending": True, "events": [], "units": {}, "cost": {}, "live": None, "book": None,
           "curve": pd.DataFrame(columns=["value", "invested", "flow", "twr"])}
    if px is None or px.empty or any(t not in px.columns for t in etfs):
        out["missing"] = [t for t in etfs if px is None or t not in px.columns]
        return out
    days = px.index[(px.index >= start) & (px.index <= last)]
    days = [d for d in days if px.loc[d, etfs].notna().all()]
    if not days:
        return out
    P = px[etfs]
    units = {t: 0.0 for t in etfs}
    cost = {t: 0.0 for t in etfs}
    first_plan = ([p for d0, p in pdays if d0 <= days[0]] or plans)[-1]
    book = RB.Book(bot or {}, px.index, first_plan.get("level") or 10, first_plan.get("sharia", False)) if BOT in tick else None
    plan = None
    pi, fi = 0, 0
    invested, twr, v_prev = 0.0, 1.0, None
    rows, events = [], []
    cur = {"d": days[0]}

    def hold(p):
        h = {t: units[t] * p[t] for t in etfs}
        if book is not None:
            h[BOT] = book.value(cur["d"])
        return h

    def trade(p, dollars):
        done = {}
        for t, x in dollars.items():
            if abs(x) < 0.005:
                continue
            if t == BOT:
                if x > 0:
                    book.deposit(x)
                else:
                    book.withdraw(-x, cur["d"])
            elif x > 0:
                units[t] += x / p[t]
                cost[t] += x
            else:
                q = min(units[t], -x / p[t])
                if units[t] > 0:
                    cost[t] *= (1 - q / units[t])
                units[t] -= q
                if units[t] < 1e-12:
                    units[t], cost[t] = 0.0, 0.0
            done[t] = round(x, 2)
        return done

    def drift(p, w):
        h = hold(p)
        tot = sum(h.values())
        if tot <= 0:
            return {}
        return {t: h.get(t, 0) / tot * 100 - w.get(t, 0) for t in set(h) | set(w)}

    prev_d = None
    pos = {d: i for i, d in enumerate(px.index)}
    for d in days:
        cur["d"] = d
        p = P.loc[d].to_dict()
        flow = 0.0
        if book is not None:                    # the bot's borrow fee belongs to the day's return
            book.fees(d)
        if v_prev:
            twr *= sum(hold(p).values()) / v_prev
        # the plan in force (a change is carried out at its own day's close)
        new_plan = None
        while pi < len(pdays) and pdays[pi][0] <= d:
            new_plan = pdays[pi][1]
            pi += 1
        if prev_d is None:
            plan = new_plan or plans[0]
            if book is not None:
                book.set_level(plan.get("level") or 10, plan.get("sharia", False), d)
            amt = float(robo["amount"])
            ev = trade(p, _buy_toward(hold(p), plan["targets"], amt))
            invested += amt
            flow += amt
            events.append({"d": d, "kind": "start", "amount": amt, "trades": ev})
        if prev_d is not None:
            if new_plan is not None and new_plan is not plan:
                plan = new_plan
                if book is not None:
                    book.set_level(plan.get("level") or 10, plan.get("sharia", False), d)
                h = hold(p)
                tot = sum(h.values())
                ev = trade(p, {t: plan["targets"].get(t, 0) / 100 * tot - h.get(t, 0) for t in tick})
                events.append({"d": d, "kind": "plan", "level": plan.get("level"), "trades": ev})
            if d.month != prev_d.month:
                amt = 0.0
                for md, a in mdays:
                    if md <= d:
                        amt = a
                if amt > 0:
                    ev = trade(p, _buy_toward(hold(p), plan["targets"], amt))
                    invested += amt
                    flow += amt
                    events.append({"d": d, "kind": "monthly", "amount": amt, "trades": ev})
        while fi < len(fdays) and fdays[fi][0] <= d:     # one-off deposits and withdrawals (the first day's too)
            _, a, note = fdays[fi]
            fi += 1
            if a > 0:
                ev = trade(p, _buy_toward(hold(p), plan["targets"], a))
                invested += a
                flow += a
                events.append({"d": d, "kind": "deposit", "amount": a, "trades": ev, "note": note})
            elif a < 0:
                h = hold(p)
                got = min(-a, sum(h.values()))
                ev = trade(p, _sell_toward(h, plan["targets"], got))
                invested -= got
                flow -= got
                events.append({"d": d, "kind": "withdraw", "amount": -got, "trades": ev, "note": note})
        if prev_d is not None:
            dr = drift(p, plan["targets"])
            mx = max((abs(x) for x in dr.values()), default=0.0)
            quarter = d.month != prev_d.month and d.month in (1, 4, 7, 10)
            out_band = [t for t, x in dr.items() if abs(x) > band(plan["targets"].get(t, 0))]
            if out_band or (quarter and mx >= 1.0):
                h = hold(p)
                tot = sum(h.values())
                ev = trade(p, {t: plan["targets"].get(t, 0) / 100 * tot - h.get(t, 0) for t in tick})
                events.append({"d": d, "kind": "rebalance", "why": "drift" if out_band else "quarter", "funds": out_band,
                               "max": mx, "trades": ev})
            elif quarter:                       # the quarterly review found every fund within a point of its target
                events.append({"d": d, "kind": "review", "max": mx})
        if book is not None:                    # the bot's own day: its exits, and on the week's first day new positions
            i = pos[d]
            sig = px.index[i - 1] if i > 0 else None
            scan = prev_d is None or d.isocalendar()[1] != prev_d.isocalendar()[1]
            book.step(d, sig, scan and plan["targets"].get(BOT, 0) > 0, fees=False)
        v = sum(hold(p).values())
        rows.append((d, v, invested, flow, twr))
        v_prev = v if v > 0 else None
        prev_d = d
    curve = pd.DataFrame(rows, columns=["d", "value", "invested", "flow", "twr"]).set_index("d")
    out.update(pending=False, curve=curve, events=events, units=units, cost=cost, plan=plan, tick=tick, book=book, vday=days[-1],
               bot_missing=book is not None and not bot)
    # today's value at the latest prices (a session under way)
    lx = P.dropna().index[-1] if len(P.dropna()) else None
    if lx is not None and lx > days[-1]:
        p = P.loc[lx].to_dict()
        val = sum(units[t] * p[t] for t in etfs) + (book.value(lx) if book is not None else 0.0)
        out["live"] = {"d": lx, "value": val, "prices": p}
        out["vday"] = lx
    out["prices"] = P.loc[days[-1]].to_dict() if out["live"] is None else out["live"]["prices"]
    return out


def holdings(rep):
    """[{t, units, price, value, cost, gain, weight, target, drift, band}] of a replay, the largest first."""
    if rep.get("pending"):
        return []
    p, plan = rep["prices"], rep["plan"]
    rows = [{"t": t, "units": rep["units"][t], "price": p[t], "value": rep["units"][t] * p[t], "cost": rep["cost"][t]} for t in rep["tick"] if t != BOT]
    if rep.get("book") is not None:
        bk = rep["book"]
        rows.append({"t": BOT, "units": None, "price": None, "value": bk.value(rep["vday"]), "cost": bk.cost})
    tot = sum(r["value"] for r in rows) or 1.0
    for r in rows:
        r["gain"] = r["value"] - r["cost"]
        r["weight"] = r["value"] / tot * 100
        r["target"] = plan["targets"].get(r["t"], 0.0)
        r["drift"] = r["weight"] - r["target"]
        r["band"] = band(r["target"])
    return sorted([r for r in rows if r["value"] > 0.005 or r["target"] > 0], key=lambda r: -r["target"] - r["weight"] / 1000)


def metrics(curve):
    """{ret (time-weighted, %), cagr (%, after a year), vol (% a year), mdd (%), days} of a replay's curve."""
    if curve is None or len(curve) < 2:
        return {}
    tw = curve["twr"].astype(float)
    r = tw.pct_change().dropna()
    days = (curve.index[-1] - curve.index[0]).days
    ret = (tw.iloc[-1] / tw.iloc[0] - 1) * 100
    out = {"ret": ret, "days": days, "vol": float(r.std() * math.sqrt(252) * 100) if len(r) > 5 else None,
           "mdd": float((tw / tw.cummax() - 1).min() * 100)}
    if days >= 365:
        out["cagr"] = ((tw.iloc[-1] / tw.iloc[0]) ** (365.25 / days) - 1) * 100
    return out


def backtest(prof, amount, monthly, px, years=5, bot=None):
    """The plan (and its benchmark) as if it had been opened `years` ago with the same money: from the first day every fund
    has a price. -> (replay, benchmark replay) or (None, None)."""
    tick = [t for t in prof["targets"] if t != BOT] + list(BENCH)
    if px is None or px.empty or any(t not in px.columns for t in tick):
        return None, None
    ok = px[tick].dropna()
    if len(ok) < 60:
        return None, None
    first = max(ok.index[0], px.index[-1] - pd.Timedelta(days=int(years * 365.25)))
    first = px.index[min(px.index.searchsorted(first), len(px.index) - 1)]
    at = PF.iso(pd.Timestamp(first).tz_localize(PF.ET).replace(hour=10).tz_convert("UTC").to_pydatetime())
    robo = {"created": at, "amount": amount, "monthly": [{"at": at, "amount": monthly}], "flows": [],
            "plans": [{"at": at, "targets": prof["targets"], "stocks": prof["stocks"], "level": prof["level"], "sharia": prof["sharia"]}]}
    sub = px.loc[px.index >= px.index[max(0, px.index.get_loc(first) - 1)]]     # one day before: the bot's first signals
    return replay(robo, sub, bot=bot), replay(robo, sub, bench=True)


def next_dates(now=None, start=None):
    """(next monthly deposit day, next quarterly review day): the first trading day of a month / quarter whose close has not
    passed yet (today's, before the close), and after `start` (the first investment's day: no deposit or review that day)."""
    after = settled_day(now).date()
    if start is not None:
        after = max(after, pd.Timestamp(start).date())

    def first_td(y, m):
        d = pd.Timestamp(y, m, 1).date()
        return d if mcal.is_trading_day(d) else mcal.next_trading_day(d)

    def nxt(months):
        y, m = after.year, after.month
        for _ in range(16):
            if m in months:
                d = first_td(y, m)
                if d > after:
                    return d
            y, m = (y + 1, 1) if m == 12 else (y, m + 1)
        return None
    return nxt(range(1, 13)), nxt((1, 4, 7, 10))


# ---------------------------------------------------------------- storage (one row of the paper bots' table)
_LOCK = threading.Lock()
_REV = {"n": 0}
SUFFIX = ":robo"


class Conflict(Exception):
    """The saved robo changed since it was read."""


def key_for(pf_key):
    return pf_key + SUFFIX


def _pb():
    import paperbots
    return paperbots


def _local_path(key):
    import hashlib
    return os.path.join(tempfile.gettempdir(), f"alturaifi_robo_{hashlib.sha256(key.encode()).hexdigest()[:20]}.json")


@st.cache_data(ttl=30, show_spinner=False)
def _load_raw(kind, rev, key):
    PB = _pb()
    if kind == "supabase":
        url, h = PB._sb()
        r = PB._request("GET", url, headers=h, params={"select": "id,params", "strategy": f"eq.{key}", "order": "id.asc", "limit": "1"})
        PB._check(r)
        rows = r.json()
        if rows:
            p = rows[0].get("params") or {}
            if isinstance(p, str):
                p = json.loads(p)
            return {"id": rows[0]["id"], "state": p.get("robo")}
        return None
    with _LOCK:
        try:
            with open(_local_path(key), encoding="utf-8") as f:
                return {"id": 0, "state": json.load(f)}
        except (OSError, ValueError):
            return None


def load(key):
    """(robo state or None, row id). Raises paperbots.StoreError."""
    raw = _load_raw(_pb().backend(), _REV["n"], key)
    return (clean(raw["state"]) if raw else None), (raw or {}).get("id")


def save(state, row_id=None, expect="any", key=None):
    PB = _pb()
    prev = state.get("rev")
    state["rev"] = int(prev or 0) + 1
    body = json.loads(json.dumps(state, default=float))
    try:
        if PB.backend() == "supabase":
            url, h = PB._sb()
            rec = {"name": "Robo portfolio", "symbol": "ROBO", "strategy": key, "params": {"robo": body},
                   "capital": float(body.get("amount") or 0), "start_date": body["created"][:10]}
            if row_id:
                q = {"id": f"eq.{int(row_id)}", "select": "id"}
                if expect != "any":
                    q["params->robo->>rev"] = "is.null" if expect is None else f"eq.{int(expect)}"
                r = PB._request("PATCH", url, headers={**h, "Prefer": "return=representation"}, params=q, data=json.dumps(rec))
                PB._check(r)
                if expect != "any" and not r.json():
                    raise Conflict()
            else:
                r = PB._request("POST", url, headers={**h, "Prefer": "return=minimal"}, data=json.dumps(rec))
                PB._check(r)
        else:
            path = _local_path(key)
            with _LOCK:
                if expect != "any":
                    try:
                        with open(path, encoding="utf-8") as f:
                            cur = json.load(f).get("rev")
                    except (OSError, ValueError):
                        cur = None
                    if cur != expect:
                        raise Conflict()
                tmp = path + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(body, f)
                os.replace(tmp, path)
    except Exception:
        state["rev"] = prev
        raise
    _REV["n"] += 1
    _load_raw.clear()


def delete(row_id, key):
    """Closes the robo portfolio: its row is removed (a new questionnaire starts a new one)."""
    PB = _pb()
    if PB.backend() == "supabase":
        if row_id:
            url, h = PB._sb()
            r = PB._request("DELETE", url, headers=h, params={"id": f"eq.{int(row_id)}", "strategy": f"eq.{key}"})
            PB._check(r)
    else:
        with _LOCK:
            try:
                os.remove(_local_path(key))
            except OSError:
                pass
    _REV["n"] += 1
    _load_raw.clear()


# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "21.3"
