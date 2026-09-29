"""
ui.py - Shared page helpers: routing, headers, sections, charts, error boundaries,
company rows with logos (click to open), news with affected companies.
"""
import re

import pandas as pd
import streamlit as st

import data
import newsiq
import theme as T
from i18n import L, is_ar, lang

PAGES = {}   # filled by app.py: key -> st.Page
CHART_CONFIG = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"]}


def goto(key):
    st.switch_page(PAGES[key])


def open_stock(sym):
    st.session_state.symbol = sym.upper()
    goto("stock")


def href(sym):
    """Link that opens a company page (works inside any HTML block)."""
    return T.stock_href(sym, lang())


def header(ic, en, ar, sub_en="", sub_ar=""):
    st.markdown(T.page_title(ic, L(en, ar), L(sub_en, sub_ar)), unsafe_allow_html=True)


def sec(ic, en, ar):
    st.markdown(T.sec(ic, L(en, ar)), unsafe_allow_html=True)


def html(s):
    st.markdown(s, unsafe_allow_html=True)


def _cell_text(v, f):
    if f is None:
        if isinstance(v, bool):
            return L("Yes", "نعم") if v else L("No", "لا")
        if isinstance(v, (int,)) and not isinstance(v, bool):
            return f"{v:,}"
        if isinstance(v, float):
            return f"{v:,.2f}"
        if isinstance(v, pd.Timestamp):
            return f"{v:%Y-%m-%d}" if (v.hour, v.minute) == (0, 0) else f"{v:%Y-%m-%d %H:%M}"
        return str(v)
    if callable(f):
        try:
            return str(f(v))
        except (ValueError, TypeError):
            return str(v)
    try:
        return f.format(v)
    except (ValueError, TypeError):
        return str(v)


_NUMLIKE = re.compile(r"^[\$\-+−]?\$?[\d,]+(\.\d+)?\s?[%×xKMBT]?$")


def _numlike(s):
    """Text columns that hold numbers (1.2B, $30.5M, 4.1×) line up on the right like numbers."""
    v = [str(x).strip() for x in s.dropna() if str(x).strip() not in ("", "—", "-")]
    return bool(v) and sum(bool(_NUMLIKE.match(x)) for x in v) >= 0.8 * len(v)


def table_html(df, fmt=None, pills=(), signed=(), cell=None, sym=None, words=None, height=None, title=None, icon="table_rows",
               chips="", min_width=None, wrap=(), index=False, logos=None):
    """A numbers table in the site's one table look (the Recent-trades panel): a box with the brand bar on its left, a muted
    header, rounded rows, numbers on the right, green / red values.
    fmt {col: '{:,.2f}' or fn}; pills: columns shown as green / red pills; signed: columns whose text is green / red by sign;
    cell {col: fn(value, row) -> html}; sym: the symbol column (logo + link to its page); words {col: (good, bad)} colours a
    text column (CALL / PUT, Buy / Sell); wrap: text columns allowed to wrap; height: scroll inside past this many px."""
    fmt, cell, words = fmt or {}, cell or {}, words or {}
    df = df.copy()
    if index:
        df = df.reset_index()
    if "Logo" in df.columns:
        if sym and logos is None:
            logos = dict(zip(df[sym], df["Logo"]))
        df = df.drop(columns=["Logo"])
    if sym and logos is None:
        try:
            logos = data.logos([s for s in df[sym].astype(str)])
        except Exception:
            logos = {}
    cols = list(df.columns)
    num = {c for c in cols if c in pills or c in signed or c in cell and c != sym
           or pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_bool_dtype(df[c]) or _numlike(df[c])}
    head = "".join(f'<th class="{"r" if c in num else ""}">{T.esc(str(c))}</th>' for c in cols)
    rows = []
    for _, r in df.iterrows():
        tds = []
        for c in cols:
            v = r[c]
            miss = v is None or (not isinstance(v, (str, list, dict)) and pd.isna(v))
            k = ["r"] if c in num else []
            if c in wrap:
                k.append("w")
            if c in cell:
                h = cell[c](v, r)
            elif miss:
                h = '<span class="m">—</span>'
            elif c == sym:
                s = str(v)
                h = (f'<a class="as" href="{T.esc(href(s))}" target="_self">{T.logo_circle(s, (logos or {}).get(s), 22)}'
                     f'<b>{T.esc(s)}</b></a>')
            else:
                t = T.esc(_cell_text(v, fmt.get(c)))
                if c in pills:
                    h = T.pbox(t, v if isinstance(v, (int, float)) else None)
                elif c in signed:
                    try:
                        h = f'<span class="{"up" if v > 0 else "dn" if v < 0 else ""}">{t}</span>'
                    except TypeError:
                        h = t
                elif c in words:
                    good, bad = words[c]
                    h = (T.pbox(t, kind="pos") if str(v) == good else T.pbox(t, kind="neg") if str(v) == bad else t)
                else:
                    h = t
            tds.append(f'<td{" class=" + chr(34) + " ".join(k) + chr(34) if k else ""}>{h}</td>')
        rows.append("<tr>" + "".join(tds) + "</tr>")
    mw = f' style="min-width:{int(min_width)}px"' if min_width else ""
    sc = f' style="max-height:{int(height)}px"' if height else ""
    hd = (f'<div class="hd"><div class="tt">{T.icon(icon)}{T.esc(title)}</div><div class="sum">{chips}</div></div>' if title else "")
    return (f'<div class="xtp">{hd}<div class="xtsc"{sc}><table class="xtbl"{mw}><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div></div>')


def table(df, **kw):
    """Show a numbers table (see table_html)."""
    html(table_html(df, **kw))


def score_bar(v, top=100):
    """A 0-100 score as a short bar with its number (for tables)."""
    try:
        f = max(0.0, min(1.0, float(v) / top))
    except (TypeError, ValueError):
        return '<span class="m">—</span>'
    return f'<span class="xbar"><i style="width:{f * 100:.0f}%"></i></span><b>{float(v):.0f}</b>'


def table_chip(label, value_html):
    return f'<span class="c">{T.esc(label)} {value_html}</span>'


def chart(fig, key=None, container=None):
    """Every Plotly chart goes through here: unified theme (no Streamlit override), clean toolbar."""
    (container or st).plotly_chart(fig, theme=None, key=key, config=CHART_CONFIG)


def safe(fn, *args, **kwargs):
    """Error boundary: one failing section never breaks the whole page."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:                      # Streamlit's rerun/stop signals are not Exceptions
        st.warning(L("This section couldn't load right now. Please try again in a minute.",
                     "تعذر تحميل هذا القسم حالياً. حاول مرة أخرى بعد دقيقة."), icon=":material/error:")
        with st.expander(L("Technical details", "تفاصيل فنية")):
            st.code(f"{type(e).__name__}: {e}"[:600])
        return None


def chips(tickers, chg, lg):
    return "".join(T.ticker_chip(s, chg.get(s, (None, None))[1], lg.get(s), href(s)) for s in tickers)


def row_list(rows, lg, show_vol=False):
    """rows: DataFrame with Symbol, Name, Price, Chg % (+ optional Rel Vol). Yahoo-style list with logo circles."""
    out = []
    for _, r in rows.iterrows():
        sub = str(r.get("Name") or "")[:28]
        right = f'<div class="px">{T.fmt_price(r["Price"])}'
        if show_vol and pd.notna(r.get("Rel Vol")):
            w = min(100, float(r["Rel Vol"]) / 5 * 100)
            right += f'<div class="meter" title="{r["Rel Vol"]:.1f}×"><span style="width:{w:.0f}%"></span></div>'
        right += "</div>"
        out.append(f'<div class="rw">{T.company(r["Symbol"], sub, lg.get(r["Symbol"]), href=href(r["Symbol"]))}{right}{T.pill(r["Chg %"])}</div>')
    return '<div class="rowlist">' + "".join(out) + "</div>"


def news_list(items, limit=20, translate=None, tag_key=None, iq=True):
    """News cards: importance score (1-10), keywords and 'affected companies' chips (logo + today's move, click to open)."""
    items = items[:limit]
    if not items:
        st.info(L("No news available right now.", "لا توجد أخبار متاحة حالياً."))
        return
    translate = is_ar() if translate is None else translate
    titles = [n["title"] for n in items]
    sums = [(n["summary"] or "")[:320] for n in items]
    translated_ok = True
    if translate:
        with st.spinner(L("Translating...", "جاري الترجمة للعربية...")):
            tr = data.translate(titles + sums)
        translated_ok = tr[:len(items)] != titles
        titles, sums = tr[:len(items)], tr[len(items):]
    tickers = sorted({s for n in items for s in n.get("tickers", [])})
    chg = data.quick_changes(tickers) if tickers else {}
    lg = data.logos(tickers) if tickers else {}
    if iq:
        newsiq.enrich(items, chg)
    out = []
    for n, t, s in zip(items, titles, sums):
        out.append(T.news_card(n, t, s, chips(n.get("tickers", []), chg, lg), L("Affected companies", "الشركات المتأثرة"),
                               ar=translate and translated_ok, tag=n.get(tag_key) if tag_key else None,
                               iq=n.get("iq") if iq else None, ui_ar=is_ar()))
    if translate and not translated_ok:
        st.caption(L("Translation service is busy right now; showing the original English. It will retry automatically.",
                     "خدمة الترجمة مشغولة حالياً؛ نعرض النص الإنجليزي الأصلي وستتم إعادة المحاولة تلقائياً."))
    html("".join(out))


def valid(key, options):
    """Forget a remembered widget value that is no longer one of the options (lists change with data)."""
    if key in st.session_state and st.session_state[key] not in list(options):
        del st.session_state[key]


def valid_multi(key, options):
    """Same for multi-select widgets: keep only the remembered values that are still options."""
    v = st.session_state.get(key)
    if isinstance(v, list):
        keep = [x for x in v if x in set(options)]
        if keep != v:
            st.session_state[key] = keep


def open_picker(symbols, key, label_en="Open a company", label_ar="افتح شركة"):
    """Selectbox + button that opens the stock page without reloading the site."""
    symbols = [s for s in dict.fromkeys(symbols) if s]
    if not symbols:
        return
    valid(f"op_{key}", symbols)
    a, b = st.columns([3, 1], vertical_alignment="bottom")
    pick = a.selectbox(L(label_en, label_ar), symbols, key=f"op_{key}")
    if b.button(L("Open", "افتح"), icon=":material/open_in_new:", key=f"opb_{key}", width="stretch"):
        open_stock(pick)


def foot():
    html(f'<div class="foot">{T.brand(".95em", "ftb", dot=True, pro="inline", color="currentColor")} · {L("Data: Yahoo Finance, FRED & BLS, may be delayed. Educational use only, not investment advice.", "البيانات: ياهو فاينانس وFRED ومكتب إحصاءات العمل وقد تكون متأخرة. للاستخدام التعليمي فقط وليست توصية استثمارية.")}</div>')


def multiselect_free(label, options, key, placeholder="", max_n=4):
    """Multiselect that also accepts typed values (newer Streamlit), with a safe fallback for older versions."""
    try:
        return st.multiselect(label, options, key=key, max_selections=max_n, accept_new_options=True, placeholder=placeholder)
    except TypeError:
        if isinstance(st.session_state.get(key), list):
            st.session_state[key] = [v for v in st.session_state[key] if v in options]
        return st.multiselect(label, options, key=key, max_selections=max_n, placeholder=placeholder)

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "13.8"
